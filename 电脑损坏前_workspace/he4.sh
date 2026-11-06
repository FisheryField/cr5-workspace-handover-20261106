L=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "=== loadParams.json ==="
cat /dobot/userdata/project/settings/function/loadParams.json
echo
echo "=== log 中 homeEncoder 全部出现(带上下文) ==="
grep -a -n "homeEncoder" $L | head -20
echo
echo "=== 上下文 (前3行/后12行) ==="
grep -a -B3 -A12 "homeEncoder" $L | head -80
echo
echo "=== 谁 READ homeEncoder / read file ==="
grep -a -o -iE ".{0,70}read file.*homeEncoder.{0,40}" $L | head -5
echo "=== libdataSvr 里该路径字符串 ==="
strings /dobot/bin/lib/libdataSvr.so.1.0.0 | grep -a "homeEncoder" | head
strings /dobot/bin/lib/libdataSvr.so.1.0.0 | grep -a "settings/function" | head -5
echo "=== loadParams 在 log ==="
grep -a -o -iE ".{0,80}loadParams.{0,80}" $L | head -5