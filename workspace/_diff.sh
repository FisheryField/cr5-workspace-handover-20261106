reset_sm() { /tmp/ecat_mbx poke eth0 $1 0x080E 00 >/dev/null 2>&1; /tmp/ecat_mbx poke eth0 $1 0x080E 01 >/dev/null 2>&1; sleep 0.02; }
OBJS="0x6064 0x6063 0x607C 0x60B0 0x60B1 0x6098 0x6060 0x6061 0x1010"
echo "obj        J6(3.1.5.0)        J1(3.2.D.8)      J2"
printf "%-10s %-16s %-16s %-16s\n" "对象" "J6" "J1" "J2"
for o in $OBJS; do
  out=""
  for st in 0x3f0 0x3eb 0x3ec; do
    reset_sm $st
    v=$(/tmp/ecat_mbx rd eth0 $st $o 0 2>&1 | grep -a "value =" | sed 's/.*value = //;s/ .*//')
    [ -z "$v" ] && v="(FAIL)"
    out="$out|$v"
  done
  printf "%-10s %-16s %-16s %-16s\n" "$o" $(echo $out | tr '|' ' ')
done
echo
echo "=== 厂商对象 0x5000~0x5007 (J6 vs J1) ==="
for o in 0x5000 0x5001 0x5002 0x5003 0x5004 0x5005 0x5006 0x5007; do
  reset_sm 0x3f0; a=$(/tmp/ecat_mbx rd eth0 0x3f0 $o 0 2>&1 | grep -a "value =" | sed 's/.*value = //')
  reset_sm 0x3eb; b=$(/tmp/ecat_mbx rd eth0 0x3eb $o 0 2>&1 | grep -a "value =" | sed 's/.*value = //')
  printf "  %-8s  J6=%-28s  J1=%s\n" "$o" "${a:-FAIL}" "${b:-FAIL}"
done
