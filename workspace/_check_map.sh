LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "=== init sdo index map 前后 25 行（看映射内容）==="
grep -a -n "init sdo index map" "$LOG" 2>/dev/null | tail -2
N=$(grep -a -n "init sdo index map" "$LOG" 2>/dev/null | tail -1 | cut -d: -f1)
if [ -n "$N" ]; then
  echo "--- 该行位于 $N，前后文 ---"
  sed -n "$((N-8)),$((N+25))p" "$LOG"
fi
echo
echo "=== 任何 sdo 相关日志（read/write/map/SDOWRCount/from codesys）==="
grep -a -oE ".{0,60}(sdo read|sdo write|sdo index map|SDOWRCount|sdo wr thd|IsWriteFromFile).{0,80}" "$LOG" 2>/dev/null | tail -25
echo
echo "=== servoParams.json 现在存在吗 ==="
ls -la /dobot/userdata/project/settings/function/servoParams.json 2>/dev/null || echo "仍不存在"
echo
echo "=== settings/function 下最近修改 ==="
ls -lat /dobot/userdata/project/settings/function/ 2>/dev/null | head -8
echo
echo "=== 当前版本 ==="
curl -s -X POST http://127.0.0.1:22000/settings/version 2>/dev/null | tr -d ' \t' | grep -E "servo[1-6]"
