TG() { /tmp/ecat_mbx poke eth0 $1 0x080E 00 >/dev/null 2>&1; /tmp/ecat_mbx poke eth0 $1 0x080E 01 >/dev/null 2>&1; sleep 0.03; }
RD() { TG $1; /tmp/ecat_mbx rd eth0 $1 $2 $3 2>&1 | grep -a "value =" | sed 's/.*value = //'; }
echo "=== J6 基线 ==="
echo "  0x6063 = $(RD 0x3f0 0x6063 0)"
echo "  0x6064 = $(RD 0x3f0 0x6064 0)"
echo "  0x607C = $(RD 0x3f0 0x607C 0)"
echo "  0x60B0 = $(RD 0x3f0 0x60B0 0)"
echo
echo "=== 写 0x607C = -16425 (即 -2.9272°/scale) ==="
TG 0x3f0
/tmp/ecat_mbx wr eth0 0x3f0 0x607C 0 -16425 2>&1 | tail -3
sleep 0.1
echo
echo "=== 写后回读 ==="
echo "  0x607C = $(RD 0x3f0 0x607C 0)"
echo "  0x6064 = $(RD 0x3f0 0x6064 0)"
echo "  0x6063 = $(RD 0x3f0 0x6063 0)"
echo
echo "=== 对照 J1 (写之前) ==="
echo "  J1 0x607C = $(RD 0x3eb 0x607C 0)"
echo "  J1 0x6064 = $(RD 0x3eb 0x6064 0)"
