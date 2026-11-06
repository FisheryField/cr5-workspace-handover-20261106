date
echo '--- 采集进程 ---'
ps | grep -E "shm_zero" | grep -v grep || echo '(未在运行)'
echo
echo '--- /tmp 下的采集目录 ---'
for d in /tmp/zero_shm_*; do
  if [ -d "$d" ]; then
    echo "$d"
    echo "   rounds=$(wc -l < $d/rounds.txt 2>/dev/null)  changes=$(wc -l < $d/changes.txt 2>/dev/null)"
    echo "   start=$(cat $d/start 2>/dev/null)  end=$(cat $d/end 2>/dev/null)"
    echo "   rounds 首末: $(head -1 $d/rounds.txt 2>/dev/null) / $(tail -1 $d/rounds.txt 2>/dev/null)"
  fi
done
echo
echo '--- 最近的标定请求（12:00 之后）---'
LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log
grep -a -oE "2026-09-23 1[12]:[0-9:.]+.*POST uri : /calibrate/home" "$LOG" 2>/dev/null | tail -3
echo
echo '--- homeEncoder.json 末条时间 ---'
grep -oE "\"time\": \"[0-9:]+\"" /dobot/userdata/project/settings/function/homeEncoder.json 2>/dev/null | tail -1
echo
echo '--- /tmp 空间 ---'
df -h /tmp | tail -1
