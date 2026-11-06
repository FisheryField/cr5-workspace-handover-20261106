for p in $(pidof codesyscontrol); do kill $p; done
for p in $(pidof gcontrol); do kill $p; done
sleep 6
ps | grep -E "codesys|gcontrol" | grep -v grep || echo "已停止"
chmod +x /tmp/ecat_zero

IDX="0x1000 0x1008 0x1009 0x100A 0x1010 0x1018 0x2000 0x2001 0x2002 0x2003 0x2004 0x2005 0x2006 0x2007 0x2008 0x2009 0x200A 0x200B 0x200C 0x200D 0x200E 0x200F 0x5000 0x5001 0x5002 0x5003 0x5004 0x5005 0x5006 0x5007 0x6000 0x6040 0x6041 0x6060 0x6061 0x6064 0x607C 0x6098 0x60B0 0x60FD"

for s in 7 8; do
  echo "##### slave $s #####"
  for i in $IDX; do
    r=$(/tmp/ecat_zero rv $s $i 0 2>/dev/null | tail -1)
    echo "$i	$r"
  done
done

echo "##### extra: 0x2001 子索引 1..20 on slave 8 #####"
for b in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do
  r=$(/tmp/ecat_zero rv 8 0x2001 $b 2>/dev/null | tail -1)
  echo "0x2001:$b	$r"
done
echo "=== SCAN DONE ==="
date
