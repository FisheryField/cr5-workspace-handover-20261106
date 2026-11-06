echo "=== 复位前 ==="
/tmp/ecat_mbx sregs eth0 0x3eb | head -3
echo "=== 翻转 SM1 Activate (0x080E): 00 -> 01 ==="
/tmp/ecat_mbx poke eth0 0x3eb 0x080E 00
sleep 0.02
/tmp/ecat_mbx poke eth0 0x3eb 0x080E 01
sleep 0.05
echo "=== 复位后 ==="
/tmp/ecat_mbx sregs eth0 0x3eb | head -3
echo
echo "=== 试着读 J1 0x6064 ==="
/tmp/ecat_mbx rd eth0 0x3eb 0x6064 0
echo "=== 再读一个 0x6063 ==="
/tmp/ecat_mbx rd eth0 0x3eb 0x6063 0
