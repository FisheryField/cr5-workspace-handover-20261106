echo "===== IDENTITY ====="
uname -a; hostname
cat /etc/os-release 2>/dev/null | head -8
echo "===== CPU/MEM ====="
uname -m; nproc; grep -m1 "model name" /proc/cpuinfo; free -m 2>/dev/null
echo "===== STORAGE ====="
df -h
echo "===== / ====="
ls -la /
echo "===== /home ====="
ls -la /home 2>/dev/null
echo "===== /root ====="
ls -la /root 2>/dev/null
echo "===== /opt ====="
ls -la /opt 2>/dev/null
echo "===== /usr/local ====="
ls -la /usr/local 2>/dev/null