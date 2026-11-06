echo "=== uptime ==="; cat /proc/uptime
echo "=== codesys log: EtherCAT 状态与错误 ==="
grep -a -o -E "(All slaves [a-z-]+|Set operational mode|InitSlaves [a-z]+|Error=[1-9][0-9]*.{0,100}|SDO write fail.{0,120}|SDO write ok: Address: 1003 Index: 16#1600 SubIndex: 0)" /dobot/userdata/project/logs/codesys/log 2>/dev/null | tail -25
echo "=== SlaveLog ==="; cat /dobot/userdata/SlaveLog 2>/dev/null | tail -25
echo "=== gcontrol log tail ==="; tail -c 700 /dobot/userdata/project/logs/gcontrol/log 2>/dev/null