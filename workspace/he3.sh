L=/dobot/bin/lib/libdataSvr.so
ls -la $L*
echo "=== offsets of key strings in libdataSvr ==="
for s in homeEncoder jointHomeState innerEncoder outEncoder encoder; do printf "%-16s " "$s"; grep -aob "$s" $L.1.0.0 2>/dev/null | head -3 | tr "\n" " "; echo; done
echo "=== strings near homeEncoder ==="
grep -aob "homeEncoder" $L.1.0.0 | head -3
echo "=== 两个 homeEncoder.json 对比 ==="
ls -la /dobot/userdata/project/settings/function/ | head -40
echo "--- CR5_sys_files ---"
ls -la /dobot/userdata/CR5_sys_files/project/settings/function/ | head -40
echo "=== 是否同一文件(inode) ==="
ls -i /dobot/userdata/project/settings/function/homeEncoder.json /dobot/userdata/CR5_sys_files/project/settings/function/homeEncoder.json 2>/dev/null
ls -la /dobot/userdata/project | head
echo "=== logs/all/log 里的 homeEncoder ==="
grep -a -o -iE ".{0,80}homeEncoder.{0,120}" /dobot/userdata/CR5_sys_files/project/logs/all/log 2>/dev/null | head -5
ls -la /dobot/userdata/CR5_sys_files/project/logs/all/ 2>/dev/null | head