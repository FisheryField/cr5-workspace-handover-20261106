echo "=== gcontrol keyword counts ==="
for k in zero calib encoder battery homing; do printf "%s: " "$k"; grep -o -a -i "$k" /dobot/userdata/project/logs/gcontrol/log* 2>/dev/null | wc -l; done
echo "=== all/log keyword counts ==="
for k in zero calib encoder battery; do printf "%s: " "$k"; grep -o -a -i "$k" /dobot/userdata/project/logs/all/log 2>/dev/null | wc -l; done
echo "=== all/log zero context ==="
grep -a -o -i -E ".{70}zero.{70}" /dobot/userdata/project/logs/all/log 2>/dev/null | head -12
echo "=== all/log encoder context ==="
grep -a -o -i -E ".{50}encoder.{50}" /dobot/userdata/project/logs/all/log 2>/dev/null | head -12
echo "=== codesys log zero/encoder ==="
grep -a -o -i -E ".{50}(zero|encoder|battery).{50}" /dobot/userdata/project/logs/codesys/log /dobot/userdata/project/logs/codesys/log.1 2>/dev/null | head -15