echo "=== codesys non-zero errors (newest 3 logs) ==="
for f in /dobot/userdata/project/logs/codesys/log /dobot/userdata/project/logs/codesys/log.1 /dobot/userdata/project/logs/codesys/log.2; do
  echo "--- $f"; grep -a -o -E ".{0,25}Error=[1-9][0-9]*.{0,150}" "$f" 2>/dev/null | head -6
done
echo "=== emergency / SDO / CoE / store ==="
grep -a -o -iE ".{0,35}(emergency|:sdo|coe |0x1010|607c|store param).{0,110}" /dobot/userdata/project/logs/codesys/log* /dobot/userdata/project/logs/gcontrol/log* 2>/dev/null | head -20
echo "=== drive / axis / 6axes messages ==="
grep -a -o -iE ".{0,25}(CmpDobot6Axes|SoftMotion|Drive=[0-9]+).{0,110}" /dobot/userdata/project/logs/codesys/log.1 2>/dev/null | head -15
echo "=== gcontrol zero/calib ==="
grep -a -o -iE ".{0,30}(zero|calib|encoder).{0,90}" /dobot/userdata/project/logs/gcontrol/log* 2>/dev/null | head -12