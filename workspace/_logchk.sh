L=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "=== 日志大小: $(wc -c < $L) ==="
echo "--- 最近 60 行 ---"
tail -60 $L
echo "--- grep sdo/key/parseAndReq ---"
tail -4000 $L | grep -aE "sdo read|sdo write|start read sdo|start write sdo|the key|parseAndReq|SDOWRCount|pack addr|exist sdo" | tail -40
