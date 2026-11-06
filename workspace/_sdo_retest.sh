for p in $(pidof codesyscontrol); do kill $p; done
for p in $(pidof gcontrol); do kill $p; done
sleep 6
ps | grep -E "codesys|gcontrol" | grep -v grep || echo STOPPED
chmod +x /tmp/ecat_zero
echo '### slave 8 (J6, 3.2.d.8)'
for a in "0x1010 0" "0x2000 1" "0x2001 14" "0x2001 18" "0x2001 19" "0x200C 3" "0x200D 8" "0x200D 9" "0x5000 1" "0x6064 0"; do
  set -- $a
  printf "  %s:%s " "$1" "$2"; /tmp/ecat_zero rv 8 $1 $2 | tail -1
done
echo '### slave 3 (J1, 3.2.d.8)'
for a in "0x1010 0" "0x2001 18" "0x200D 8"; do
  set -- $a
  printf "  %s:%s " "$1" "$2"; /tmp/ecat_zero rv 3 $1 $2 | tail -1
done
echo '### 顺带：0x5000-0x5007 全扫 slave 8（旧固件里这组是 0）'
for i in 0x5000 0x5001 0x5002 0x5003 0x5004 0x5005 0x5006 0x5007; do
  printf "  %s:0 " "$i"; /tmp/ecat_zero rv 8 $i 0 | tail -1
done
