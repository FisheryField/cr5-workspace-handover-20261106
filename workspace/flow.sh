echo "=== 哪些二进制包含 /calibrate/ 或 /properties/ ==="
for f in /dobot/bin/gcontrol /dobot/bin/logServer $(ls /dobot/bin/lib/*.so* 2>/dev/null) $(ls /home/ftp/.lib/*.so 2>/dev/null); do
  n=$(strings "$f" 2>/dev/null | grep -c -E "/calibrate/|/properties/|/settings/function")
  [ "$n" -gt 0 ] && echo "$n  $f"
done
echo "=== 含 /calibrate/home 的文件 ==="
for f in /dobot/bin/gcontrol /dobot/bin/logServer $(ls /dobot/bin/lib/*.so* 2>/dev/null) $(ls /home/ftp/.lib/*.so 2>/dev/null) $(ls /usr/lib/libCmp*.so 2>/dev/null); do
  if strings "$f" 2>/dev/null | grep -q "/calibrate/home"; then echo "HIT: $f"; fi
done
echo "=== 22000 端口的进程与加载的库 ==="
netstat -tlnp 2>/dev/null | grep 22000
for p in $(pidof codesyscontrol); do echo "pid=$p"; cat /proc/$p/maps 2>/dev/null | grep -oE "/[^ ]+\.so[^ ]*" | sort -u | head -30; done
echo "=== fifo / 共享内存 ==="
ls -la /dobot/bin/fifo* /dev/shm 2>/dev/null | head -20
echo "=== 进程列表(关键) ==="
ps | grep -E "codesys|gcontrol|logServer|dataSvr|redis" | grep -v grep