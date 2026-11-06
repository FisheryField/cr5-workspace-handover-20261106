printf "%-16s %-22s %-22s %-22s\n" "站(轴/固件)" "FPRD 0x1a30" "FPRD 0x1800" "FPRD 0x1200"
for st in 0x3eb:J1/3.2.D.8 0x3ec:J2 0x3ed:J3 0x3ee:J4 0x3ef:J5 0x3f0:J6/3.1.5.0; do
  a=${st%%:*}; n=${st##*:}
  r1=$(/tmp/ecat_mbx peek eth0 $a 0x1a30 8 2>&1 | head -1 | sed 's/.*wkc=/wkc=/;s/ pkt.*//')
  r2=$(/tmp/ecat_mbx peek eth0 $a 0x1800 8 2>&1 | head -1 | sed 's/.*wkc=/wkc=/;s/ pkt.*//')
  r3=$(/tmp/ecat_mbx peek eth0 $a 0x1200 8 2>&1 | head -1 | sed 's/.*wkc=/wkc=/;s/ pkt.*//')
  printf "%-16s %-22s %-22s %-22s\n" "$n" "$r1" "$r2" "$r3"
done
echo
echo "=== 写方向 FPWR 0x1800 逐站 ==="
for st in 0x3eb 0x3ec 0x3ed 0x3ee 0x3ef 0x3f0; do
  printf "  %s : " $st
  /tmp/ecat_mbx poke eth0 $st 0x1800 0000000000000000
done
