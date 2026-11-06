echo '=== 库文件 ==='
ls -la /dobot/bin/lib/ 2>/dev/null | head -20
echo '=== codesyscontrol 谁在拉起 ==='
grep -n -i "codesys" /dobot/bin/dobot.sh 2>/dev/null | head -20
echo '=== 是否有看门狗/守护 ==='
ps 2>/dev/null | head -30
echo '=== 进程父子关系 ==='
for p in $(ps -o pid= 2>/dev/null | head -40); do
  ppid=$(awk '{print $4}' /proc/$p/stat 2>/dev/null)
  cmd=$(tr '\0' ' ' < /proc/$p/cmdline 2>/dev/null | cut -c1-60)
  [ -n "$cmd" ] && echo "pid=$p ppid=$ppid $cmd"
done | head -30
