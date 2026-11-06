chmod +x /tmp/ecat_mbx
echo "########## J1 (3.2.D.8) ##########"
for o in 0x6064 0x6063 0x607C 0x6098 0x6060 0x6061 0x60B0 0x6065 0x6066; do
  printf "  %-8s : " $o
  /tmp/ecat_mbx sdo2 eth0 0x3eb $o 0 2>&1 | grep -aE "==>|value" | tr -d '\n'
  echo
done
echo
echo "########## J6 (3.1.5.0) ##########"
for o in 0x6064 0x6063 0x607C 0x6098 0x6060 0x6061 0x60B0 0x6065 0x6066; do
  printf "  %-8s : " $o
  /tmp/ecat_mbx sdo2 eth0 0x3f0 $o 0 2>&1 | grep -aE "==>|value" | tr -d '\n'
  echo
done
