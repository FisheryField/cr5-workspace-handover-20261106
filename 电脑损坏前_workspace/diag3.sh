echo "=== gcontrol log 里的错误/报警关键词 ==="
grep -a -o -iE ".{0,40}(error|fail|alarm|fault|timeout).{0,60}" /dobot/userdata/project/logs/gcontrol/log 2>/dev/null | tail -12
echo "=== codesys log 里的 Error!=0 ==="
grep -a -o -E "Class=[0-9]+, Error=[1-9][0-9]*.{0,120}" /dobot/userdata/project/logs/codesys/log 2>/dev/null | tail -8
echo "=== codesys 启动时的 SDO write 记录（看有没有写 607C）==="
grep -a -o -E "SDO write (ok|fail): Address: [0-9]+ Index: 16#[0-9A-F]+ SubIndex: [0-9]+ Data: 16#[0-9A-F]+" /dobot/userdata/project/logs/codesys/log 2>/dev/null | sort -u | head -40
echo "=== SavePos / recipe ==="
ls -la /home/ftp/PlcLogic/Recipe/ 2>/dev/null