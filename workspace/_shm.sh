echo "=== /dev/shm ==="
ls -la /dev/shm 2>/dev/null | head -30
echo
echo "=== 相关进程 ==="
ps w 2>/dev/null | grep -aiE "codesys|dataSvr|mTool|servo|ethercat|dobot" | grep -av grep
echo
echo "=== eth0 状态 ==="
ifconfig eth0 2>/dev/null | head -5
echo
echo "=== 共享内存段（/proc/*/maps 中的 shm）==="
for p in /proc/[0-9]*; do
  if grep -qas "/dev/shm\|/SYSV" $p/maps 2>/dev/null; then
    echo "pid $(basename $p) : $(cat $p/comm 2>/dev/null)"
    grep -as "/dev/shm\|/SYSV" $p/maps | sort -u | head -6
  fi
done
