TG() { /tmp/ecat_mbx poke eth0 $1 0x080E 00 >/dev/null 2>&1; /tmp/ecat_mbx poke eth0 $1 0x080E 01 >/dev/null 2>&1; sleep 0.03; }
echo "=== 还原 J6 0x607C = 0 ==="
TG 0x3f0
/tmp/ecat_mbx wr eth0 0x3f0 0x607C 0 0 2>&1 | tail -2
sleep 0.1
echo "=== 回读确认 ==="
TG 0x3f0
/tmp/ecat_mbx rd eth0 0x3f0 0x607C 0 2>&1 | grep -a "value ="
echo
echo "=== 顺便取一组对照数据（J1/J2/J6 的 0x6040/0x6041/0x6060/0x6061）==="
for st in 0x3f0 0x3eb 0x3ec; do
  echo "--- 站 $st ---"
  for o in 0x6040 0x6041 0x6060 0x6061 0x6098; do
    TG $st
    v=$(/tmp/ecat_mbx rd eth0 $st $o 0 2>&1 | grep -a "value =" | sed 's/.*value = //;s/ .*//')
    printf "    %-8s = %s\n" "$o" "${v:-FAIL}"
  done
done
