touch -d "2026-09-18 19:26:30" /tmp/ref1 2>/dev/null || echo "touch -d 不支持"
touch -d "2026-09-18 19:20:00" /tmp/ref0 2>/dev/null
touch -d "2026-09-18 17:00:00" /tmp/ref2 2>/dev/null
echo "=== 19:26:30 之后被修改的文件(排除日志/proc/sys/tmp) ==="
find / -xdev -newer /tmp/ref1 -type f ! -path "/proc/*" ! -path "/sys/*" ! -path "/tmp/*" ! -path "/dev/*" ! -path "*/logs/*" ! -name "log*" 2>/dev/null | head -60
echo
echo "=== 19:20 之后(含启动) ==="
find / -xdev -newer /tmp/ref0 -type f ! -path "/proc/*" ! -path "/sys/*" ! -path "/tmp/*" ! -path "/dev/*" ! -path "*/logs/*" ! -name "log*" 2>/dev/null | head -80
echo
echo "=== 17:00 之后(本次上电以来) ==="
find / -xdev -newer /tmp/ref2 -type f ! -path "/proc/*" ! -path "/sys/*" ! -path "/tmp/*" ! -path "/dev/*" ! -path "*/logs/*" ! -name "log*" 2>/dev/null | head -80
echo
echo "=== gcontrol 里的 EncoderData 符号 ==="
strings /dobot/bin/gcontrol | grep -a -i -E "updateEncoderData|EncoderData|jointHomeState|innerEncoder" | head
echo "=== libdataSvr 里的 EncoderData 符号 ==="
strings /dobot/bin/lib/libdataSvr.so.1.0.0 | grep -a -i -E "updateEncoderData|EncoderData|jointHomeState|innerEncoder" | head