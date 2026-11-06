echo "=== J6 刷写全过程（11:11-11:13 完整窗口）==="
grep -a -E "2026-09-22 11:1[123]" /mToolServer/mToolServer.log 2>/dev/null | grep -a -vE "get /protocol/version|get /update/singleStatus" | head -45

echo
echo "=== 身份级对比：slave 7 (3.1.5.0) vs slave 8 (3.2.d.8) ==="
chmod +x /tmp/ecat_zero
for s in 7 8; do
  echo "--- slave $s ---"
  for a in "0x1008 0" "0x1009 0" "0x100A 0" "0x1018 2" "0x1018 3" "0x1018 4"; do
    set -- $a
    echo -n "  $1:$2  "; /tmp/ecat_zero rv $s $1 $2 | tail -1
  done
done

echo
echo "=== 全轴 0x1018:03 Revision（固件版本通常编码在此）==="
for s in 3 4 5 6 7 8; do echo -n "  slave $s  "; /tmp/ecat_zero rv $s 0x1018 3 | tail -1; done
echo
echo "=== 全轴 0x100A:00 ==="
for s in 3 4 5 6 7 8; do echo -n "  slave $s  "; /tmp/ecat_zero rv $s 0x100A 0 | tail -1; done
