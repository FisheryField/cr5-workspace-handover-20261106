echo "=== /proc/sysvipc/shm ==="
cat /proc/sysvipc/shm
echo
echo "=== codesyscontrol(378) 映射的 SYSV 段 ==="
grep -a "SYSV" /proc/378/maps | sort -u
echo
echo "=== 找 robot_map shm key 文件 ==="
find /dobot /tmp /home -iname "*shm*key*" -o -iname "*robot_map*" 2>/dev/null | head -20
echo
echo "=== libdataSvr 里 shm key 相关字符串 ==="
strings -n 6 /dobot/bin/lib/libdataSvr.so 2>/dev/null | grep -aiE "shm_key|shm key|shmid|robot_map" | head -20
