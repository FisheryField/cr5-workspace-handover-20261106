for off in 0x1800 0x1a30 0x0800; do
  ok=0
  for i in 1 2 3 4 5 6 7 8 9 10; do
    r=$(/tmp/ecat_mbx peek eth0 0x3f0 $off 8 2>&1 | head -1)
    case "$r" in *"wkc=1"*) ok=$((ok+1));; esac
  done
  echo "off=$off  10 次里 wkc=1 的次数 = $ok"
done
echo
echo "=== 再看 0x0800 (寄存器区) 连打 10 次 ==="
ok=0
for i in 1 2 3 4 5 6 7 8 9 10; do
  r=$(/tmp/ecat_mbx peek eth0 0x3f0 0x0800 8 2>&1 | head -1)
  case "$r" in *"wkc=1"*) ok=$((ok+1));; esac
done
echo "0x0800 -> $ok / 10"
