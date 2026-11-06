#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <unistd.h>
#if defined(__has_include)
#  if __has_include("soem/soem.h")
#    include "soem/soem.h"
#  else
#    include "soem/ethercat.h"
#  endif
#else
#  include "soem/ethercat.h"
#endif
static int32_t rd32(int s, uint16_t i, uint8_t b, int *ok){uint8_t x[8];memset(x,0,8);int z=4,t=3000;int w=ec_SDOread(s,i,b,FALSE,&z,x,&t);*ok=(w>0);return (int32_t)((uint32_t)x[0]|((uint32_t)x[1]<<8)|((uint32_t)x[2]<<16)|((uint32_t)x[3]<<24));}
static uint16_t rd16(int s, uint16_t i, uint8_t b, int *ok){uint8_t x[4];memset(x,0,4);int z=2,t=3000;int w=ec_SDOread(s,i,b,FALSE,&z,x,&t);*ok=(w>0);return (uint16_t)(x[0]|(x[1]<<8));}
static uint8_t  rd8 (int s, uint16_t i, uint8_t b, int *ok){uint8_t x[4];memset(x,0,4);int z=1,t=3000;int w=ec_SDOread(s,i,b,FALSE,&z,x,&t);*ok=(w>0);return x[0];}
static int wr32(int s,uint16_t i,uint8_t b,int32_t v){int z=4,t=3000;return ec_SDOwrite(s,i,b,FALSE,z,&v,t);}
static int wr16(int s,uint16_t i,uint8_t b,uint16_t v){int z=2,t=3000;return ec_SDOwrite(s,i,b,FALSE,z,&v,t);}
static int wr8 (int s,uint16_t i,uint8_t b,uint8_t  v){int z=1,t=3000;return ec_SDOwrite(s,i,b,FALSE,z,&v,t);}
static void one(int s,uint16_t i,uint8_t b){int ok;int32_t v=rd32(s,i,b,&ok);
    if(ok)printf("  0x%04X:%02d = %d\n",i,b,v); else printf("  0x%04X:%02d = <FAIL>\n",i,b); fflush(stdout);}
static void home(int s){
    int ok;
    printf("=== home test on slave %d ===\n", s);
    printf("--- before ---\n");
    one(s,0x6041,0); one(s,0x6040,0); one(s,0x6060,0); one(s,0x6061,0);
    one(s,0x6098,0); one(s,0x6064,0); one(s,0x6063,0); one(s,0x607C,0); one(s,0x60B0,0);
    printf("1) 清除 RxPDO 映射 (0x1600:00 = 0) -> wkc=%d\n", wr8(s,0x1600,0,0)); fflush(stdout);
    printf("2) 清故障 cw=0x0080 -> wkc=%d\n", wr16(s,0x6040,0,0x0080)); usleep(300000);
    printf("3) cw=0x0000 -> wkc=%d\n", wr16(s,0x6040,0,0x0000)); usleep(300000);
    printf("4) 切回零模式 0x6060=6 -> wkc=%d\n", wr8(s,0x6060,0,6)); usleep(300000);
    printf("5) 回零方式 0x6098=35 -> wkc=%d\n", wr8(s,0x6098,0,35)); usleep(300000);
    printf("6) cw=0x0006 shutdown -> wkc=%d\n", wr16(s,0x6040,0,0x0006)); usleep(400000);
    printf("7) cw=0x0007 switch on -> wkc=%d\n", wr16(s,0x6040,0,0x0007)); usleep(400000);
    printf("8) cw=0x000F enable op -> wkc=%d\n", wr16(s,0x6040,0,0x000F)); usleep(400000);
    printf("   状态: sw=0x%04X mode=%d\n", rd16(s,0x6041,0,&ok), rd8(s,0x6061,0,&ok));
    printf("9) cw=0x001F 启动回零\n"); printf("   wkc=%d\n", wr16(s,0x6040,0,0x001F)); fflush(stdout);
    for (int i=0;i<40;i++){
        uint16_t sw = rd16(s,0x6041,0,&ok);
        printf("   [%02d] sw=0x%04X  mode=%d  reached=%d  homingOK=%d\n", i, sw, rd8(s,0x6061,0,&ok),
               (sw>>10)&1, (sw>>12)&1); fflush(stdout);
        if (sw & 0x1000) break;
        if ((sw & 0x0008) == 0 && i > 3) { printf("   !! 故障位已置位，停止\n"); break; }
        usleep(250000);
    }
    printf("--- after ---\n");
    one(s,0x6041,0); one(s,0x6060,0); one(s,0x6061,0);
    one(s,0x6064,0); one(s,0x6063,0); one(s,0x607C,0); one(s,0x60B0,0);
    printf("=== done ===\n");
}
int main(int argc,char**argv){
    const char*m=(argc>1)?argv[1]:"read";
    if(!ec_init((char*)"eth0")){printf("ec_init FAILED\n");return 2;}
    if(ec_config_init(FALSE)<=0){printf("no slaves\n");ec_close();return 3;}
    printf("slaves=%d mode=%s\n",ec_slavecount,m);fflush(stdout);
    if(strcmp(m,"read")==0){for(int s=1;s<=ec_slavecount;s++)if(ec_slave[s].eep_id==0x121){one(s,0x6064,0);one(s,0x607C,0);one(s,0x60B0,0);}}
    else if(strcmp(m,"home")==0&&argc>=3){home(atoi(argv[2]));}
    else if(strcmp(m,"rv")==0&&argc>=5){one(atoi(argv[2]),(uint16_t)strtol(argv[3],NULL,0),(uint8_t)atoi(argv[4]));}
    else if(strcmp(m,"wv")==0&&argc>=6){int s=atoi(argv[2]);uint16_t i=(uint16_t)strtol(argv[3],NULL,0);uint8_t b=(uint8_t)atoi(argv[4]);int32_t v=(int32_t)strtol(argv[5],NULL,0);printf("write 0x%04X:%02d=%d -> wkc=%d\n",i,b,v,wr32(s,i,b,v));}
    else printf("usage: read | home <slave> | rv <s> <idx> <sub> | wv <s> <idx> <sub> <val>\n");
    ec_close();return 0;
}
