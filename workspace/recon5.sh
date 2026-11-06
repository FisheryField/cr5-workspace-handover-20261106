echo "=== version.json ==="; cat /mToolServer/control/version.json
echo "=== supportRules.json ==="; cat /mToolServer/control/supportRules.json
echo "=== toolUtils.sh ==="; cat /mToolServer/control/toolUtils.sh
echo "=== checkPO.sh ==="; cat /mToolServer/control/checkPO.sh
echo "=== operatePO.sh ==="; cat /mToolServer/control/operatePO.sh
echo "=== 352run.sh ==="; cat /mToolServer/control/352run.sh
echo "=== 450run.sh ==="; cat /mToolServer/control/450run.sh
echo "=== mToolServer.log head 25 ==="; head -25 /mToolServer/mToolServer.log
echo "=== controlRunProcess.log head 15 ==="; head -15 /mToolServer/controlRunProcess.log
echo "=== overTurn files ==="; cat /mToolServer/overTurn/SavePos.txt; echo "---"; cat /mToolServer/overTurn/SaveAxesValue.AxesValues.txtrecipe
echo "=== ftp/affinity ==="; ls -la /home/ftp/affinity; cat /home/ftp/affinity/Start.sh
echo "=== PlcLogic ==="; ls -la /home/ftp/PlcLogic
echo "=== userdata/codesys ==="; ls -la /dobot/userdata/codesys
echo "=== root log file ==="; cat /log