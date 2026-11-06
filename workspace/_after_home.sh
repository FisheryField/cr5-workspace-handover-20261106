TG() { /tmp/ecat_mbx poke eth0 0x3f0 0x080E 00 >/dev/null 2>&1; /tmp/ecat_mbx poke eth0 0x3f0 0x080E 01 >/dev/null 2>&1; sleep 0.03; }
echo "=== 还原 J6 0x1600:00 = 20 ==="
for i in 1 2 3 4 5 6; do
  TG; /tmp/ecat_mbx wr eth0 0x3f0 0x1600 0 20 >/dev/null 2>&1; sleep 0.05
  TG; v=$(/tmp/ecat_mbx rd eth0 0x3f0 0x1600 0 2>&1 | grep -a "value =" | sed 's/.*value = //;s/ (.*//')
  echo "  尝试 $i : 0x1600:00 = ${v:-读不到}"
  [ "$v" = "20" ] && { echo "  ==> 已还原"; break; }
done
echo
echo "=== SOEM 初始化后, ecat_mbx 扫描是否变可靠? 扫 J6 标准对象 ==="
/tmp/ecat_mbx scan eth0 0x3f0 0x6040 0x6041 0
/tmp/ecat_mbx scan eth0 0x3f0 0x6060 0x6064 0
echo
echo "=== 扫 J6 厂商段 0x5000..0x5010 ==="
/tmp/ecat_mbx scan eth0 0x3f0 0x5000 0x5010 0
