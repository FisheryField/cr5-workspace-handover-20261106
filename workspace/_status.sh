date; echo "uptime: $(cat /proc/uptime)"
echo '--- 进程 ---'
ps | grep -E "codesyscontrol|gcontrol" | grep -v grep
echo '--- /tmp 下的 zeroprobe 产物 ---'
ls -d /tmp/zp_* /tmp/*probe* 2>/dev/null
echo '--- 各产物时间与内容长度 ---'
for d in /tmp/zp_*; do
  [ -d "$d" ] && echo "$d  state.txt=$(wc -c < $d/state.txt 2>/dev/null)B  start=$(head -2 $d/state.txt | tail -1)"
done
echo '--- 最近的标定/重启痕迹 ---'
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log
grep -a -oE "2026-09-23 1[12]:[0-9:.]+.*POST uri : /calibrate/home" "$LOG" 2>/dev/null | tail -2
echo '--- homeEncoder.json 末条 ---'
grep -oE "\"time\": \"[0-9:]+\"" /dobot/userdata/project/settings/function/homeEncoder.json 2>/dev/null | tail -1
