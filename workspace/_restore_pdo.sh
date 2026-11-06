TG() { /tmp/ecat_mbx poke eth0 0x3f0 0x080E 00 >/dev/null 2>&1; /tmp/ecat_mbx poke eth0 0x3f0 0x080E 01 >/dev/null 2>&1; sleep 0.03; }
for i in 1 2 3 4 5 6 7 8 9 10 11 12; do
  TG
  /tmp/ecat_mbx wr eth0 0x3f0 0x1600 0 20 >/dev/null 2>&1
  sleep 0.05
  TG
  v=$(/tmp/ecat_mbx rd eth0 0x3f0 0x1600 0 2>&1 | grep -a "value =" | sed 's/.*value = //;s/ (.*//')
  echo "  尝试 $i : 0x1600:00 = ${v:-读不到}"
  if [ "$v" = "20" ]; then echo "  ==> 已还原"; break; fi
done
echo
echo "=== 顺带确认其他站未被改动 ==="
for st in 0x3eb 0x3ec 0x3f0; do
  TG_ST=$st
  /tmp/ecat_mbx poke eth0 $st 0x080E 00 >/dev/null 2>&1; /tmp/ecat_mbx poke eth0 $st 0x080E 01 >/dev/null 2>&1; sleep 0.03
  v=$(/tmp/ecat_mbx rd eth0 $st 0x1600 0 2>&1 | grep -a "value =" | sed 's/.*value = //;s/ (.*//')
  echo "  $st 0x1600:00 = ${v:-读不到}"
done
