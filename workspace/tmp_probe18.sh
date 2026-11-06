echo "=== A libs"
ls -la /dobot/bin/lib/ 2>/dev/null | head -40
echo "=== A find algs"
find /dobot -maxdepth 4 -name "*algs*" 2>/dev/null | head -20
echo "=== A find libdata"
find /dobot -maxdepth 4 -name "libdata*" -o -maxdepth 4 -name "libgcontrol*" 2>/dev/null | head -20
echo "=== A homeEncoder"
cat /dobot/userdata/project/settings/function/homeEncoder.json | tail -60
echo "=== A DONE"