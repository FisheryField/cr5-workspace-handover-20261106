echo "=== 连读 J6 多个对象 ==="
for o in 0x6064 0x6063 0x607C 0x6098 0x6060 0x6061 0x60B0 0x6065 0x6066; do
  printf "J6 %-8s : " $o
  /tmp/ecat_mbx rd eth0 0x3f0 $o 0 2>&1 | grep -aE "==>|value" | tr '\n' ' '
  echo
done
