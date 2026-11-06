#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#if defined(__has_include)
#  if __has_include("soem/soem.h")
#    include "soem/soem.h"
#  else
#    include "soem/ethercat.h"
#  endif
#else
#  include "soem/ethercat.h"
#endif

static void rd(int slave, const char *label, uint16_t idx, uint8_t sub) {
    uint8_t buf[8];
    memset(buf, 0, sizeof buf);
    int sz = 4;
    int tmo = 3000;
    int wkc = ec_SDOread(slave, idx, sub, FALSE, &sz, buf, &tmo);
    if (wkc > 0) {
        int32_t v = (int32_t)((uint32_t)buf[0] | ((uint32_t)buf[1] << 8) |
                              ((uint32_t)buf[2] << 16) | ((uint32_t)buf[3] << 24));
        printf("  0x%04X:%02X  %-26s = %12d   (0x%08X) size=%d\n",
               idx, sub, label, v, (uint32_t)v, sz);
    } else {
        printf("  0x%04X:%02X  %-26s = READ FAIL (wkc=%d)\n", idx, sub, label, wkc);
    }
    fflush(stdout);
}

int main(int argc, char **argv) {
    const char *ifname = (argc > 1) ? argv[1] : "eth0";
    printf("=== SOEM EtherCAT SDO READER (READ-ONLY) ===\n");
    fflush(stdout);
    if (!ec_init(ifname)) { printf("ec_init(%s) FAILED\n", ifname); return 2; }
    printf("ec_init(%s) ok\n", ifname);
    if (ec_config_init(FALSE) <= 0) { printf("no slaves found\n"); ec_close(); return 3; }
    printf("slaves found: %d\n\n", ec_slavecount);
    for (int s = 1; s <= ec_slavecount; s++) {
        printf("slave %d: %-24s man=0x%08X id=0x%08X rev=0x%08X\n", s,
               ec_slave[s].name, ec_slave[s].eep_man, ec_slave[s].eep_id, ec_slave[s].eep_rev);
    }
    printf("\n");
    for (int s = 1; s <= ec_slavecount; s++) {
        if (ec_slave[s].eep_id != 0x121) { printf("slave %d skipped (not DS121)\n", s); continue; }
        printf("----- servo slave %d (%s) -----\n", s, ec_slave[s].name);
        rd(s, "position actual value",   0x6064, 0);
        rd(s, "home offset",             0x607C, 0);
        rd(s, "modes of operation",      0x6060, 0);
        rd(s, "modes display",           0x6061, 0);
        rd(s, "homing method",           0x6098, 0);
        rd(s, "pos encoder res num",     0x608F, 1);
        rd(s, "pos encoder res den",     0x608F, 2);
        rd(s, "gear ratio motor",        0x6091, 1);
        rd(s, "gear ratio shaft",        0x6091, 2);
        rd(s, "sw pos limit min",        0x607D, 1);
        rd(s, "sw pos limit max",        0x607D, 2);
        rd(s, "profile velocity",        0x6081, 0);
        rd(s, "supported drive modes",   0x6502, 0);
        printf("\n");
    }
    ec_close();
    printf("done\n");
    return 0;
}
