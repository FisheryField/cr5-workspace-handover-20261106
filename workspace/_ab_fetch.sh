#!/bin/sh
touch /tmp/ab_stop
sleep 2
echo "=== meta ==="; cat /tmp/ab_meta.txt
echo "raw=$(wc -c < /tmp/ab_raw.bin)  ts=$(wc -l < /tmp/ab_ts.txt)"
echo "=== 控制器日志里最近的标定/控制模式事件 ==="
grep -a -E 'calibrate/home|controlMode|servo calihome|HomeNumdone : 6' /dobot/userdata/CR5_sys_files/project/logs/all/log 2>/dev/null | tail -25
cd /tmp && tar czf /tmp/ab_data.tgz ab_raw.bin ab_ts.txt ab_meta.txt
ls -la /tmp/ab_data.tgz
