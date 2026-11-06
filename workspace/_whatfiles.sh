touch -d "2026-09-23 11:26:45" /tmp/ref_a 2>/dev/null
touch -d "2026-09-23 11:27:05" /tmp/ref_b 2>/dev/null
echo '=== 11:26:45~11:27:05（11:26:52 那次标定的窗口）内被修改的文件 ==='
find /dobot /home /etc /opt /tmp -type f -newer /tmp/ref_a ! -newer /tmp/ref_b 2>/dev/null | grep -v "/logs/" | grep -v lost+found | head -40
echo
echo '=== 同期被修改的目录 ==='
find /dobot /home /etc -type d -newer /tmp/ref_a ! -newer /tmp/ref_b 2>/dev/null | head -20
echo
echo '=== 参考：整个 9/23 20:00 之后被改过的、非 logs 的文件（近 1 小时）==='
touch -d "2026-09-23 11:00:00" /tmp/ref_c 2>/dev/null
find /dobot /home /etc /opt -type f -newer /tmp/ref_c 2>/dev/null | grep -v "/logs/" | grep -v lost+found | head -40
rm -f /tmp/ref_a /tmp/ref_b /tmp/ref_c
