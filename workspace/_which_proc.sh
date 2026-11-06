GP=$(pidof gcontrol | awk '{print $1}'); CP=$(pidof codesyscontrol | awk '{print $1}')
echo "=== libdataSvr 加载在哪个进程？ ==="
for p in $GP $CP; do
  n=$(grep -c "libdataSvr" /proc/$p/maps 2>/dev/null)
  echo "  PID $p ($(tr '\0' ' ' < /proc/$p/cmdline | cut -c1-40)): libdataSvr 映射 $n 处"
done
echo
echo "=== libdataSvr 的可写段（数据/BSS，C++ 对象就在这）==="
for p in $GP $CP; do
  grep "libdataSvr" /proc/$p/maps 2>/dev/null | grep -E "rw" | head -5 | sed "s/^/  PID $p: /"
done
echo
echo "=== 版本接口（换个写法）==="
wget -qO- --post-data='' http://127.0.0.1:22000/settings/version 2>/dev/null | head -20
echo
echo "=== 今天标零次数与最近三条记录 ==="
grep -c "POST uri : /calibrate/home" /dobot/userdata/CR5_sys_files/project/logs/all/log 2>/dev/null
grep -oE "\"time\": \"[0-9:]+\"" /dobot/userdata/project/settings/function/homeEncoder.json 2>/dev/null | tail -3
