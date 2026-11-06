echo "=== interpreters on controller ==="
for x in python python3 python2 perl awk busybox; do
  p=$(which $x 2>/dev/null)
  echo "$x -> ${p:-none}"
done
python -V 2>&1 | head -1
python3 -V 2>&1 | head -1
echo "=== python modules ==="
python -c "import zlib,struct,sys,hashlib; print('ok', sys.version)" 2>&1 | head -2
echo "=== getconf / page ==="
getconf PAGE_SIZE 2>/dev/null
echo "=== tmpfs free ==="
df -h /tmp
echo "=== total RAM ==="
head -3 /proc/meminfo
echo "=== END ==="
