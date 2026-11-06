#!/bin/sh
# 只读：从轮转日志 log.1 找版本行（本次 14:13 开机的版本标记可能在 log.1 尾部）
LOG1=/dobot/userdata/CR5_sys_files/project/logs/all/log.1
echo "===== log.1 尾部的 settVersion ====="
grep -a "settVersion" $LOG1 | tail -14
echo
echo "===== log.1 尾部 servo 版本相关 ====="
grep -a "slave.*version\|servo.*:.*3\." $LOG1 | tail -8
