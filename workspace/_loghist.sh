L=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "日志总行数: $(wc -l < $L)"
echo "sdo read,slave 出现次数 : $(grep -ac 'sdo read,slave' $L)"
echo "sdo read fail  出现次数 : $(grep -ac 'sdo read fail' $L)"
echo "sdo write      出现次数 : $(grep -ac 'sdo write' $L)"
echo "create thread to read sdo: $(grep -ac 'create thread to read sdo' $L)"
echo "create thread to write sdo: $(grep -ac 'create thread to write sdo' $L)"
echo "the key .* is error 次数 : $(grep -ac 'is error' $L)"
echo
echo "--- 最早的 sdo read 记录（前 6 条）---"
grep -an 'sdo read,slave' $L | head -6
echo
echo "--- 最早的 sdo read fail（前 6 条）---"
grep -an 'sdo read fail' $L | head -6
echo
echo "--- write sdo 相关全部 ---"
grep -a 'sdo write\|start write sdo' $L | head -10
echo
echo "--- 是否有过任何 index 非 0 的读 ---"
grep -a 'sdo read,slave' $L | grep -av 'index=0,subIndex=0' | head -10
