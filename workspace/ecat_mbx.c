/* ecat_mbx.c --- 最小 EtherCAT 邮箱 SDO 工具（原始帧注入，不改从站状态）
 * 用法:
 *   ecat_mbx rd    <if> <st> <idx> <sub>          SDO upload
 *   ecat_mbx wr    <if> <st> <idx> <sub> <i32>    SDO download
 *   ecat_mbx sregs <if> <st>                      打印 SM0..SM3 寄存器 (0x0800..0x081F)
 *   ecat_mbx peek  <if> <st> <off> <len>          原始 FPRD
 *   ecat_mbx poke  <if> <st> <off> <hexbytes>     原始 FPWR (如 poke eth0 0x3f0 0x080E 00)
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <unistd.h>
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <sys/time.h>
#include <net/if.h>
#include <netinet/in.h>
#include <linux/if_packet.h>
#include <linux/if_ether.h>
#include <time.h>

#define MBX_WR_OFF 0x1800
#define MBX_RD_OFF 0x1a20   /* ★ 入口地址必须落在 0x1a30 之前: 访问检查只看起始地址 */
#define MBX_RD_PAD 16
#define MBX_RD_LEN (MBXSZ + MBX_RD_PAD)
#define MBXSZ      512

static int sfd = -1;
static unsigned char ourmac[6];
static unsigned char IDX = 0x5a;
static unsigned char lastframe[64];
static int lastpkttype = -1;

static unsigned char chan_of(uint16_t st){
    switch(st){ case 0x03ee: return 0x13; case 0x03ef: return 0x73;
                case 0x03f0: return 0x23; default: return 0x33; }
}
static uint64_t now_ms(void){ struct timespec ts; clock_gettime(CLOCK_MONOTONIC,&ts);
    return (uint64_t)ts.tv_sec*1000ULL + ts.tv_nsec/1000000ULL; }

static int EXTRA = 0;   /* 1 = 追加一个尾随 BRD 数据报(模仿控制器的多数据报帧) */
static int build(unsigned char *f, int cmd, uint16_t st, uint16_t off,
                 const unsigned char *data, int n)
{
    int tot = 10 + n + 2 + (EXTRA ? 14 : 0);
    memset(f, 0, 14+2+tot);
    memset(f, 0xff, 6);
    memcpy(f+6, ourmac, 6);
    f[12]=0x88; f[13]=0xa4;
    f[14]=(unsigned char)(tot & 0xff);
    f[15]=(unsigned char)(((tot>>8)&0x07) | 0x10);
    int o = 16;
    f[o++]=cmd; f[o++]=IDX;
    f[o++]=(unsigned char)(st & 0xff);  f[o++]=(unsigned char)(st>>8);
    f[o++]=(unsigned char)(off & 0xff); f[o++]=(unsigned char)(off>>8);
    f[o++]=(unsigned char)(n & 0xff);   f[o++]=(unsigned char)((n>>8)&0x07);
    if (EXTRA) f[o-1] |= 0x80;            /* more=1 */
    f[o++]=0; f[o++]=0;
    if (data) memcpy(f+o, data, n);
    o += n; f[o++]=0; f[o++]=0;
    if (EXTRA) {                          /* 尾随: BRD 读 AL 状态, 和控制器的帧一样 */
        f[o++]=0x07; f[o++]=0xae;
        f[o++]=0x00; f[o++]=0x00; f[o++]=0x30; f[o++]=0x01;
        f[o++]=0x02; f[o++]=0x00; f[o++]=0; f[o++]=0;
        f[o++]=0; f[o++]=0; f[o++]=0; f[o++]=0;
    }
    return 14+2+tot;
}
static int roundtrip(int cmd, uint16_t st, uint16_t off,
                     const unsigned char *tx, unsigned char *out, int n, int *got)
{
    unsigned char f[6144], r[6144];
    int fl = build(f, cmd, st, off, tx, n);
    if (send(sfd, f, fl, 0) != fl) { perror("send"); return -1; }
    uint64_t t0 = now_ms(); *got = 0;
    while (now_ms() - t0 < 300) {
        struct sockaddr_ll from; socklen_t fl = sizeof from;
        int rl = recvfrom(sfd, r, sizeof r, 0, (struct sockaddr*)&from, &fl);
        if (rl < 28) continue;
        /* ★ 关键：AF_PACKET 会把自己发出的帧也投递回来，必须剔除，
         *   否则会在从站处理之前就匹配到 wkc=0 的空帧。 */
        if (from.sll_pkttype == PACKET_OUTGOING) continue;
        if (r[12]!=0x88 || r[13]!=0xa4) continue;
        if (memcmp(r+6, ourmac, 6) != 0) continue;
        int flen = (r[14] | ((r[15]&0x07)<<8));
        int o = 16, end = 16+flen;
        while (o+12 <= end && o+12 <= rl) {
            int id = r[o+1];
            int dl = (r[o+6] | ((r[o+7]&0x07)<<8));
            int more = (r[o+7]>>7)&1;
            if (id == IDX) {
                /* ★ 地址也要一致，否则可能是匹配到别的设备的帧 */
                if (r[o+2]!=(unsigned char)(st&0xff)  || r[o+3]!=(unsigned char)(st>>8) ||
                    r[o+4]!=(unsigned char)(off&0xff) || r[o+5]!=(unsigned char)(off>>8)) {
                    o += 12 + dl; if (!more) break; continue;
                }
                int wkc = r[o+10+dl] | (r[o+11+dl]<<8);
                if (out && dl>0) memcpy(out, r+o+10, dl);
                memcpy(lastframe, r, 64); lastpkttype = from.sll_pkttype;
                *got=1; return wkc;
            }
            o += 12 + dl;
            if (!more) break;
        }
    }
    return -1;
}
static void mk_frame16(unsigned char *m, uint8_t ch, uint8_t sdocmd,
                       uint16_t index, uint8_t sub, int32_t val)
{
    memset(m, 0, MBXSZ);
    m[0]=0x0a; m[1]=0x00; m[2]=0; m[3]=0; m[4]=0; m[5]=ch;
    m[6]=0x00; m[7]=0x20;
    m[8]=sdocmd;
    m[9]=(unsigned char)(index & 0xff); m[10]=(unsigned char)(index >> 8);
    m[11]=sub;
    m[12]=(unsigned char)val; m[13]=(unsigned char)(val>>8);
    m[14]=(unsigned char)(val>>16); m[15]=(unsigned char)(val>>24);
}
static void hexdump(const unsigned char *b, int n){
    for (int i=0;i<n;i++){ if(i%16==0) printf("\n    %04x: ", i);
        printf("%02x ", b[i]); }
    printf("\n");
}


/* ---- diag: 一次完整事务的全过程观测 ---- */
static void smstat(uint16_t st, const char*tag)
{
    unsigned char tx[16], r[16]; int got;
    memset(tx,0,sizeof tx);
    roundtrip(0x04, st, 0x0800, tx, r, 16, &got);
    if (got)
        printf("  [%s] SM0(0x1800) ctrl=%02x st=%02x act=%02x | SM1(0x1a30) ctrl=%02x st=%02x act=%02x\n",
               tag, r[4], r[5], r[6], r[12], r[13], r[14]);
    else printf("  [%s] <读 SM 寄存器失败>\n", tag);
}
static int cmd_diag(const char *ifn, uint16_t st, uint16_t idx, uint8_t sub, int mode)
{
    unsigned char mf[MBXSZ], r[MBXSZ], tx[MBXSZ]; int got;
    (void)ifn;
    printf("== diag st=0x%04x idx=0x%04x:%u mode=%d ==\n", st, idx, sub, mode);
    smstat(st, "初始");
    mk_frame16(mf, chan_of(st), 0x40, idx, sub, 0);
    printf("  请求帧: "); for(int i=0;i<16;i++) printf("%02x ", mf[i]); printf("\n");

    if (mode == 1) {
        /* 先写 body 再写 header（SOEM 风格，长度字段最后落地） */
        roundtrip(0x05, st, MBX_WR_OFF+6, mf+6, NULL, MBXSZ-6, &got);
        usleep(500);
        roundtrip(0x05, st, MBX_WR_OFF, mf, NULL, 6, &got);
    } else {
        roundtrip(0x05, st, MBX_WR_OFF, mf, NULL, MBXSZ, &got);
    }
    usleep(100); smstat(st, "写后0.1ms");
    usleep(900); smstat(st, "写后1ms");
    usleep(4000); smstat(st, "写后5ms");
    usleep(15000); smstat(st, "写后20ms");

    printf("  --- 轮询读邮箱 ---\n");
    for (int k = 0; k < 60; k++) {
        memset(tx, 0, MBXSZ);
        int wkc = roundtrip(0x04, st, MBX_RD_OFF, tx, r, MBXSZ, &got);
        if (wkc >= 0 && (r[0] || r[7])) {
            printf("  poll %2d wkc=%d: ", k, wkc);
            for (int i=0;i<16;i++) printf("%02x ", r[i]);
            printf("\n");
            if (r[0]==0x0a && r[7]==0x30) { printf("  ==> 收到应答!\n"); return 0; }
        }
        usleep(2000);
    }
    printf("  ==> 60 次轮询无应答\n");
    return 1;
}



/* ---- FMMU 映射 + 逻辑地址读写：绕开配置地址对 SM 区的访问保护 ---- */
static int fmmu_set(uint16_t st, int n, uint32_t logaddr, uint16_t phys, uint16_t len, int iswrite)
{
    unsigned char r[16]; int got;
    memset(r, 0, sizeof r);
    r[0]=(unsigned char)logaddr; r[1]=(unsigned char)(logaddr>>8);
    r[2]=(unsigned char)(logaddr>>16); r[3]=(unsigned char)(logaddr>>24);
    r[4]=(unsigned char)len; r[5]=(unsigned char)(len>>8);
    r[6]=0x00; r[7]=0x07;
    r[8]=(unsigned char)phys; r[9]=(unsigned char)(phys>>8);
    r[10]=0x00;
    r[11]= iswrite ? 0x01 : 0x00;
    r[12]=0x00;
    roundtrip(0x05, st, (uint16_t)(0x0600 + n*16), r, NULL, 16, &got);
    r[12]=0x01;
    int w = roundtrip(0x05, st, (uint16_t)(0x0600 + n*16), r, NULL, 16, &got);
    printf("  FMMU%d: log=0x%08X -> phys=0x%04X len=%d %s  activate wkc=%d\n",
           n, logaddr, phys, len, iswrite?"WR":"RD", w);
    return w;
}
static int cmd_sdo2(uint16_t st, uint16_t idx, uint8_t sub, int iswrite, int32_t *val)
{
    unsigned char mf[MBXSZ], r[256], tx[256];
    int got, k;
    const uint32_t LA_RD = 0x00010000, LA_WR = 0x00020000;
    printf("== FMMU 方式 SDO st=0x%04x idx=0x%04x:%u %s ==\n", st, idx, sub, iswrite?"WRITE":"READ");
    fmmu_set(st, 3, LA_RD, 0x1a30, 64, 0);
    fmmu_set(st, 4, LA_WR, 0x1a30, 64, 1);
    for (int attempt = 0; attempt < 3; attempt++) {
        mk_frame16(mf, chan_of(st), (unsigned char)(iswrite?0x23:0x40), idx, sub, iswrite?*val:0);
        roundtrip(0x05, st, MBX_WR_OFF, mf, NULL, MBXSZ, &got);
        for (k = 0; k < 200; k++) {
            memset(tx, 0, sizeof tx);
            int wkc = roundtrip(0x0a, (uint16_t)(LA_RD & 0xffff), (uint16_t)(LA_RD >> 16), tx, r, 64, &got);
            if (wkc >= 0 && r[0] == 0x0a && r[7] == 0x30 &&
                r[9] == (unsigned char)(idx & 0xff) && r[10] == (unsigned char)(idx >> 8) && r[11] == sub) {
                int32_t dv = (int32_t)((uint32_t)r[12] | ((uint32_t)r[13]<<8) |
                                       ((uint32_t)r[14]<<16) | ((uint32_t)r[15]<<24));
                printf("  ==> OK attempt=%d poll=%d sdo=0x%02x\n", attempt, k, r[8]);
                printf("  应答: ");
                for (int i=0;i<16;i++) printf("%02x ", r[i]);
                printf("\n  value = %d (0x%08X)\n", dv, (uint32_t)dv);
                if (iswrite) *val = dv;
                unsigned char z[8]; memset(z, 0, 8);
                int w2 = roundtrip(0x0b, (uint16_t)(LA_WR & 0xffff), (uint16_t)(LA_WR >> 16), z, NULL, 6, &got);
                printf("  释放SM1(LWR 6B 0) wkc=%d\n", w2);
                return 0;
            }
            usleep(500);
        }
        printf("  attempt %d 无应答\n", attempt);
    }
    printf("  ==> FAILED\n");
    return -1;
}


/* ---- 批量扫描对象字典：每条读之前用 SM1 释放，输出 "idx sub value" ---- */
static int sdo_once(uint16_t st, uint16_t idx, uint8_t sub, int32_t *out, unsigned char *raw)
{
    unsigned char mf[MBXSZ], r[256], tx[256], z[1], o[1];
    int got, k, att;
    memset(z, 0, 1); memset(o, 0, 1); o[0] = 0x01;
    roundtrip(0x05, st, 0x080E, z, NULL, 1, &got);
    roundtrip(0x05, st, 0x080E, o, NULL, 1, &got);
    usleep(30000);          /* ★ 翻转后必须给从站时间, 否则邮箱不响应 */
    for (att = 0; att < 4; att++) {
        mk_frame16(mf, chan_of(st), 0x40, idx, sub, 0);
        roundtrip(0x05, st, MBX_WR_OFF, mf, NULL, MBXSZ, &got);
        for (k = 0; k < 150; k++) {
            memset(tx, 0, sizeof tx);
            int wkc = roundtrip(0x04, st, MBX_RD_OFF, tx, r, 64, &got);
            const unsigned char *M = r + MBX_RD_PAD;
            if (wkc >= 0 && M[0] == 0x0a && M[7] == 0x30 &&
                M[9] == (unsigned char)(idx & 0xff) && M[10] == (unsigned char)(idx >> 8) && M[11] == sub) {
                if (raw) memcpy(raw, M, 24);
                int32_t dv = (int32_t)((uint32_t)M[12] | ((uint32_t)M[13]<<8) |
                                       ((uint32_t)M[14]<<16) | ((uint32_t)M[15]<<24));
                if (M[8] == 0x80) { *out = dv; return -3; }
                *out = dv;
                return 0;
            }
            usleep(400);
        }
    }
    *out = 0;
    return -1;
}
static int cmd_scan(uint16_t st, uint16_t ilo, uint16_t ihi, int submax)
{
    int32_t v; unsigned char raw[24];
    printf("# scan st=0x%04x idx 0x%04x..0x%04x sub 0..%d\n", st, ilo, ihi, submax);
    for (uint16_t idx = ilo; idx <= ihi; idx++) {
        for (int sub = 0; sub <= submax; sub++) {
            int rc = sdo_once(st, idx, (uint8_t)sub, &v, raw);
            if (rc == 0) printf("%04x %d %d OK\n", idx, sub, v);
            else if (rc == -3) printf("%04x %d %d ABORT\n", idx, sub, v);
        }
    }
    printf("# end\n");
    return 0;
}


/* ---- SDO 写 (下载) ---- */
static int sdo_wr1(uint16_t st, uint16_t idx, uint8_t sub, int32_t val)
{
    unsigned char mf[MBXSZ], r[256], tx[256], z[1], o[1];
    int got, k, att;
    memset(z,0,1); memset(o,0,1); o[0]=0x01;
    roundtrip(0x05, st, 0x080E, z, NULL, 1, &got);
    roundtrip(0x05, st, 0x080E, o, NULL, 1, &got);
    usleep(30000);
    for (att = 0; att < 4; att++) {
        mk_frame16(mf, chan_of(st), 0x23, idx, sub, val);
        roundtrip(0x05, st, MBX_WR_OFF, mf, NULL, MBXSZ, &got);
        for (k = 0; k < 150; k++) {
            memset(tx, 0, sizeof tx);
            int wkc = roundtrip(0x04, st, MBX_RD_OFF, tx, r, 64, &got);
            const unsigned char *M = r + MBX_RD_PAD;
            if (wkc >= 0 && M[0]==0x0a && M[7]==0x30 &&
                M[9]==(unsigned char)(idx&0xff) && M[10]==(unsigned char)(idx>>8) && M[11]==sub) {
                if (M[8] == 0x60) return 0;
                if (M[8] == 0x80) return -3;
                return -2;
            }
            usleep(400);
        }
    }
    return -1;
}
static void RP(uint16_t st, const char *label, uint16_t idx, uint8_t sub, int *rc, int32_t *val)
{
    int32_t v = 0;
    int r = sdo_once(st, idx, sub, &v, NULL);
    if (rc) *rc = r; if (val) *val = v;
    if (r == 0)        printf("    %-22s 0x%04X:%u = %d (0x%X)\n", label, idx, sub, v, (unsigned)v);
    else if (r == -3)  printf("    %-22s 0x%04X:%u = ABORT 0x%08X\n", label, idx, sub, (unsigned)v);
    else               printf("    %-22s 0x%04X:%u = <无应答>\n", label, idx, sub);
}
static int cmd_home(uint16_t st)
{
    int32_t v = 0; int rc;
    printf("=== 标准 CiA402 回零 (纯 SDO)  st=0x%04x ===\n", st);
    printf("  --- before ---\n");
    RP(st, "0x6041 状态字",      0x6041, 0, NULL, NULL);
    RP(st, "0x6040 控制字",      0x6040, 0, NULL, NULL);
    RP(st, "0x6060 模式",        0x6060, 0, NULL, NULL);
    RP(st, "0x6061 模式显示",    0x6061, 0, NULL, NULL);
    RP(st, "0x6098 回零方式",    0x6098, 0, NULL, NULL);
    RP(st, "0x6064 位置实际值",  0x6064, 0, NULL, NULL);
    RP(st, "0x607C Home offset", 0x607C, 0, NULL, NULL);

    int32_t n_map = 0, n_ps = 0;
    printf("  [0] 读/清 RxPDO 映射\n");
    if (sdo_once(st, 0x1600, 0, &n_map, NULL) == 0) {
        printf("      0x1600:00 (RxPDO 映射条目数) = %d\n", n_map);
        printf("      -> 清 0x1600:00 = 0 : %s\n",
               sdo_wr1(st, 0x1600, 0, 0) == 0 ? "OK" : "失败");
        usleep(200000);
    } else printf("      0x1600:00 读不到, 跳过清映射\n");
    if (sdo_once(st, 0x1C12, 1, &n_ps, NULL) == 0) printf("      0x1C12:01 (RxPDO 分配) = %d\n", n_ps);
    RP(st, "0x6060 模式(清映射后)", 0x6060, 0, NULL, NULL);

    printf("  [1] 0x6060 <- 6 (回零模式)\n");
    rc = sdo_wr1(st, 0x6060, 0, 6);  printf("      -> %s\n", rc==0?"OK":(rc==-3?"ABORT":"无应答")); usleep(120000);
    printf("  [2] 0x6098 <- 35 (当前位置即原点)\n");
    rc = sdo_wr1(st, 0x6098, 0, 35); printf("      -> %s\n", rc==0?"OK":(rc==-3?"ABORT":"无应答")); usleep(120000);

    printf("  [3] 控制字序列 0x0006 -> 0x0007 -> 0x000F\n");
    rc = sdo_wr1(st, 0x6040, 0, 0x0006); printf("      0x0006 -> %s\n", rc==0?"OK":(rc==-3?"ABORT":"无应答")); usleep(150000);
    rc = sdo_wr1(st, 0x6040, 0, 0x0007); printf("      0x0007 -> %s\n", rc==0?"OK":(rc==-3?"ABORT":"无应答")); usleep(150000);
    rc = sdo_wr1(st, 0x6040, 0, 0x000F); printf("      0x000F -> %s\n", rc==0?"OK":(rc==-3?"ABORT":"无应答")); usleep(150000);

    printf("  [4] 0x6040 <- 0x001F (bit4 启动回零)\n");
    rc = sdo_wr1(st, 0x6040, 0, 0x001F); printf("      -> %s\n", rc==0?"OK":(rc==-3?"ABORT":"无应答"));

    printf("  [5] 轮询状态字\n");
    for (int i = 0; i < 40; i++) {
        v = 0;
        rc = sdo_once(st, 0x6041, 0, &v, NULL);
        if (rc == 0) {
            printf("      [%02d] sw=0x%04X  reached(b10)=%d  homingOK(b12)=%d  fault(b3)=%d\n",
                   i, (unsigned)(v & 0xffff), (int)((v>>10)&1), (int)((v>>12)&1), (int)((v>>3)&1));
            if ((v >> 12) & 1) break;
        } else printf("      [%02d] <状态字读不到>\n", i);
        usleep(300000);
    }

    printf("  [6] 清 bit4: 0x6040 <- 0x000F\n");
    sdo_wr1(st, 0x6040, 0, 0x000F); usleep(150000);

    printf("  --- after ---\n");
    RP(st, "0x6041 状态字",      0x6041, 0, NULL, NULL);
    RP(st, "0x6061 模式显示",    0x6061, 0, NULL, NULL);
    RP(st, "0x6064 位置实际值",  0x6064, 0, &rc, &v);
    RP(st, "0x6063 内部位置",    0x6063, 0, NULL, NULL);
    RP(st, "0x607C Home offset", 0x607C, 0, NULL, NULL);

    printf("  [7] 0x6060 <- 8 (切回 CSP)\n");
    rc = sdo_wr1(st, 0x6060, 0, 8); printf("      -> %s\n", rc==0?"OK":(rc==-3?"ABORT":"无应答"));
    RP(st, "0x6060 模式",        0x6060, 0, NULL, NULL);
    if (n_map > 0) {
        printf("  [8] 还原 0x1600:00 <- %d : %s\n", n_map,
               sdo_wr1(st, 0x1600, 0, n_map) == 0 ? "OK" : "失败");
        RP(st, "0x1600:00 还原后", 0x1600, 0, NULL, NULL);
    }
    return 0;
}

int main(int argc, char **argv)
{
    if (argc < 4) {
        printf("usage:\n  %s rd    <if> <st> <idx> <sub>\n  %s wr    <if> <st> <idx> <sub> <i32>\n"
               "  %s sregs <if> <st>\n  %s peek  <if> <st> <off> <len>\n  %s poke  <if> <st> <off> <hex>\n",
               argv[0],argv[0],argv[0],argv[0],argv[0]);
        return 1;
    }
    const char *m = argv[1];
    const char *ifn = argv[2];
    uint16_t st = (uint16_t)strtol(argv[3], NULL, 0);
    sfd = socket(AF_PACKET, SOCK_RAW, htons(ETH_P_ALL));
    if (sfd < 0) { perror("socket"); return 2; }
    struct ifreq ifr; memset(&ifr,0,sizeof ifr);
    strncpy(ifr.ifr_name, ifn, IFNAMSIZ-1);
    if (ioctl(sfd, SIOCGIFINDEX, &ifr) < 0) { perror("SIOCGIFINDEX"); return 3; }
    struct sockaddr_ll sll; memset(&sll,0,sizeof sll);
    sll.sll_family=AF_PACKET; sll.sll_protocol=htons(ETH_P_ALL); sll.sll_ifindex=ifr.ifr_ifindex;
    if (bind(sfd,(struct sockaddr*)&sll,sizeof sll) < 0) { perror("bind"); return 4; }
    memset(&ifr,0,sizeof ifr); strncpy(ifr.ifr_name, ifn, IFNAMSIZ-1);
    if (ioctl(sfd, SIOCGIFHWADDR, &ifr) < 0) { perror("SIOCGIFHWADDR"); return 5; }
    memcpy(ourmac, ifr.ifr_hwaddr.sa_data, 6);
    { const char *e = getenv("ECAT_IDX"); if (e) IDX = (unsigned char)strtol(e,NULL,0);
      const char *a = getenv("ECAT_ADR"); if (a) EXTRA = atoi(a); }
    struct timeval tv = {0, 60000};
    setsockopt(sfd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof tv);

    if (strcmp(m,"home")==0) {
        int rc = cmd_home(st);
        close(sfd); return rc;
    }
    if (strcmp(m,"scan")==0) {
        uint16_t lo=(uint16_t)strtol(argv[4],NULL,0), hi=(uint16_t)strtol(argv[5],NULL,0);
        int sm=(argc>6)?atoi(argv[6]):0;
        int rc = cmd_scan(st, lo, hi, sm);
        close(sfd); return rc;
    }
    if (strcmp(m,"sdo2")==0 || strcmp(m,"sdo2w")==0) {
        uint16_t i2 = (uint16_t)strtol(argv[4], NULL, 0);
        uint8_t  s2 = (uint8_t)strtol(argv[5], NULL, 0);
        int wr = (strcmp(m,"sdo2w")==0);
        int32_t v2 = (argc>6 && wr) ? (int32_t)strtol(argv[6], NULL, 0) : 0;
        int rc = cmd_sdo2(st, i2, s2, wr, &v2);
        close(sfd); return rc==0 ? 0 : 20;
    }
    if (strcmp(m,"lrd")==0 || strcmp(m,"lwr")==0) {
        uint32_t la = (uint32_t)strtoul(argv[4], NULL, 0);
        unsigned char tx[512], rr[512]; int got;
        memset(tx, 0, sizeof tx);
        unsigned char b[256]; int bn = 0;
        int n = 0;
        if (strcmp(m,"lwr")==0) {
            const char *hx = argv[5];
            for (const char *p = hx; p[0] && p[1] && bn < 256; p += 2) { char t[3]={p[0],p[1],0}; b[bn++] = (unsigned char)strtol(t,NULL,16); }
            n = bn;
        } else n = atoi(argv[5]);
        int wkc = roundtrip(strcmp(m,"lwr")==0 ? 0x0b : 0x0a,
                            (uint16_t)(la & 0xffff), (uint16_t)(la >> 16),
                            strcmp(m,"lwr")==0 ? b : tx, rr, n, &got);
        printf("%s log=0x%08X len=%d wkc=%d\n", m, la, n, wkc);
        if (got && strcmp(m,"lwr")!=0) hexdump(rr, n<64?n:64);
        close(sfd); return 0;
    }
    if (strcmp(m,"diag")==0) {
        uint16_t di=(uint16_t)strtol(argv[4],NULL,0);
        uint8_t  ds=(uint8_t)strtol(argv[5],NULL,0);
        int dmode = (argc>6)?atoi(argv[6]):0;
        return cmd_diag(ifn, st, di, ds, dmode);
    }
    if (strcmp(m,"sregs")==0) {
        unsigned char tx[64], r[64]; int got;
        memset(tx,0,sizeof tx);
        int wkc = roundtrip(0x04, st, 0x0800, tx, r, 32, &got);
        printf("st=0x%04x SM 寄存器 0x0800..0x081F  (wkc=%d)\n", st, wkc);
        if (got) {
            for (int i=0;i<4;i++){
                unsigned char*p = r+i*8;
                int start = p[0]|(p[1]<<8), len = p[2]|(p[3]<<8);
                printf("  SM%d: start=0x%04x len=%-5d ctrl=0x%02x status=0x%02x activate=0x%02x pdi=0x%02x\n",
                       i, start, len, p[4], p[5], p[6], p[7]);
            }
        }
        /* 顺带看看 AL 状态和 ESC 信息 */
        memset(tx,0,sizeof tx);
        wkc = roundtrip(0x04, st, 0x0130, tx, r, 16, &got);
        if (got) printf("  AL status(0x0130) = 0x%04x   AL control(0x0120) = 0x%04x\n",
                        r[0]|(r[1]<<8), r[8]|(r[9]<<8));
        return 0;
    }
    if (strcmp(m,"peekx")==0 || strcmp(m,"pokex")==0) {
        EXTRA = 1;
        if (strcmp(m,"pokex")==0) {
            uint16_t off=(uint16_t)strtol(argv[4],NULL,0);
            const char*hx=argv[5]; unsigned char b[768]; int n=0;
            for (const char*p=hx; p[0]&&p[1]&&n<768; p+=2){char t[3]={p[0],p[1],0}; b[n++]=(unsigned char)strtol(t,NULL,16);}
            int got; int wkc = roundtrip(0x05, st, off, b, NULL, n, &got);
            printf("pokex st=0x%04x off=0x%04x %dB -> wkc=%d\n", st, off, n, wkc);
            return 0;
        }
        uint16_t off=(uint16_t)strtol(argv[4],NULL,0); int len=atoi(argv[5]);
        unsigned char tx[2048], r[2048]; int got;
        memset(tx,0,sizeof tx);
        int wkc = roundtrip(0x04, st, off, tx, r, len, &got);
        printf("peekx st=0x%04x off=0x%04x len=%d wkc=%d\n", st, off, len, wkc);
        if (got) hexdump(r, len<48?len:48);
        return 0;
    }
    if (strcmp(m,"peek")==0) {
        uint16_t off=(uint16_t)strtol(argv[4],NULL,0); int len=atoi(argv[5]);
        unsigned char tx[2048], r[2048]; int got;
        memset(tx,0,sizeof tx);
        int wkc = roundtrip(0x04, st, off, tx, r, len, &got);
        printf("peek st=0x%04x off=0x%04x len=%d wkc=%d pkttype=%d\n", st, off, len, wkc, lastpkttype);
        if (got) hexdump(r, len<64?len:64);
        if (got) { printf("  收到帧头 32B: "); for(int i=0;i<32;i++) printf("%02x ", lastframe[i]); printf("\n"); }
        return 0;
    }
    if (strcmp(m,"poke")==0) {
        uint16_t off=(uint16_t)strtol(argv[4],NULL,0);
        const char*hx=argv[5]; unsigned char b[64]; int n=0;
        for (const char*p=hx; p[0] && p[1] && n<64; p+=2) {
            char t[3]={p[0],p[1],0}; b[n++]=(unsigned char)strtol(t,NULL,16);
        }
        int got;
        int wkc = roundtrip(0x05, st, off, b, NULL, n, &got);
        printf("poke st=0x%04x off=0x%04x %d 字节 -> wkc=%d\n", st, off, n, wkc);
        return 0;
    }

    /* ---- SDO ---- */
    uint16_t idx=(uint16_t)strtol(argv[4],NULL,0);
    uint8_t  sub=(uint8_t)strtol(argv[5],NULL,0);
    int is_wr = (strcmp(m,"wr")==0);
    int32_t v = (argc>6 && is_wr) ? (int32_t)strtol(argv[6],NULL,0) : 0;
    printf("st=0x%04x idx=0x%04x:%u %s\n", st, idx, sub, is_wr?"WRITE":"READ");
    fflush(stdout);

    unsigned char mf[MBXSZ], r[MBX_RD_LEN], tx[MBX_RD_LEN];
    int got, k;
    for (int attempt=0; attempt<4; attempt++) {
        mk_frame16(mf, chan_of(st), (unsigned char)(is_wr?0x23:0x40), idx, sub, is_wr?v:0);
        roundtrip(0x05, st, MBX_WR_OFF, mf, NULL, MBXSZ, &got);
        for (k=0;k<250;k++) {
            memset(tx,0,MBX_RD_LEN);
            int wkc = roundtrip(0x04, st, MBX_RD_OFF, tx, r, MBX_RD_LEN, &got);
            const unsigned char *M = r + MBX_RD_PAD;
            if (wkc>=0 && M[0]==0x0a && M[7]==0x30 &&
                M[9]==(idx&0xff) && M[10]==(idx>>8) && M[11]==sub) {
                printf("  ==> OK  attempt=%d poll=%d  sdo=0x%02x  data=%02x %02x %02x %02x\n",
                       attempt, k, M[8], M[12],M[13],M[14],M[15]);
                printf("  应答: "); for(int i=0;i<16;i++) printf("%02x ", M[i]); printf("\n");
                int32_t dv = (int32_t)((uint32_t)M[12]|((uint32_t)M[13]<<8)|((uint32_t)M[14]<<16)|((uint32_t)M[15]<<24));
                if (!is_wr) printf("  value = %d (0x%08X)\n", dv, (uint32_t)dv); else v = dv;
                return 0;
            }
            usleep(800);
        }
        printf("  attempt %d 无应答\n", attempt);
    }
    printf("  ==> FAILED\n");
    return 20;
}