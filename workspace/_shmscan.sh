echo "=== 1) 发一个独特的读请求 (J6, H01.17 = 0x2001:18) ==="
wget -q -O - --post-data='{"body":[{"key":"addr200118","servoNum":"J6"}]}'   --header='Content-Type: application/json'   http://127.0.0.1:22000/settings/readServoParams 2>&1 | head -2
echo
sleep 1
echo "=== 2) 取 378 的 SYSV 映射地址 ==="
grep -a "SYSV" /proc/378/maps | awk '{print $1, $6}' | sort -u > /tmp/sysv.txt
wc -l < /tmp/sysv.txt
head -5 /tmp/sysv.txt
echo
echo "=== 3) 逐个段扫模式 080000000120000012000000 ==="
PAT="080000000120000012000000"
n=0
while read -r range dev; do
  start=${range%%-*}
  n=$((n+1))
  [ $n -gt 30 ] && break
  hit=$(dd if=/proc/378/mem bs=4096 skip=$((0x$start/4096)) count=146 2>/dev/null | od -An -tx1 -v | tr -d ' \n' | grep -o "$PAT" | head -1)
  if [ -n "$hit" ]; then echo "  ★ 命中! 段 $dev  起始 0x$start"; fi
done < /tmp/sysv.txt
echo "扫描完成 ($n 个段)"
