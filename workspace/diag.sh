echo "=== controller date ==="; date
echo "=== files touched in last 12h ==="
find /dobot /home/ftp /opt /etc -type f -mmin -720 2>/dev/null | grep -v "/logs/all/" | grep -v lost+found | head -60
echo "=== Recipe dir mtimes ==="; ls -la --time-style=full-iso /home/ftp/PlcLogic/Recipe/ 2>/dev/null || ls -la /home/ftp/PlcLogic/Recipe/
echo "=== properties mtimes ==="; ls -la --time-style=full-iso /dobot/userdata/project/properties/ 2>/dev/null | head -20 || ls -la /dobot/userdata/project/properties/ | head -20
echo "=== newest gcontrol log: zero/calib grep ==="; grep -i -a -o -E ".{60}(zero|calib|encoder).{60}" /dobot/userdata/project/logs/gcontrol/log 2>/dev/null | head -10
echo "=== gcontrol log tail ==="; tail -c 1200 /dobot/userdata/project/logs/gcontrol/log 2>/dev/null
echo "=== codesys log tail ==="; tail -c 1500 /dobot/userdata/project/logs/codesys/log 2>/dev/null
echo "=== SavePos / AxesValue now ==="; cat /home/ftp/PlcLogic/Recipe/SaveAxesValue.AxesValues.txtrecipe 2>/dev/null; echo "--- SavePos hex ---"; od -A d -t x1 /home/ftp/PlcLogic/Recipe/SavePos.txt 2>/dev/null | head -4