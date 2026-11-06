echo "=== 控制器二进制里的 API 路由 ==="
for f in /dobot/bin/gcontrol /dobot/bin/lib/libdataSvr.so.1.0.0 /dobot/bin/lib/libdataSvrPlugin.so.1.0.0 /dobot/bin/lib/libprocessPlugin.so.1.0.0 /dobot/bin/logServer; do
  echo "--- $f"
  strings "$f" 2>/dev/null | grep -E "^/(calibrate|interface|properties|settings|protocol|panel|process|project|backup|firmware)[a-zA-Z0-9_/]*$" | sort -u | head -80
done
echo "=== 含 save/store/persist/flash/zero 的路由或关键字 ==="
for f in /dobot/bin/gcontrol /dobot/bin/lib/libdataSvr.so.1.0.0 /dobot/bin/lib/libdataSvrPlugin.so.1.0.0 /dobot/bin/lib/libprocessPlugin.so.1.0.0; do
  echo "--- $f"
  strings "$f" 2>/dev/null | grep -iE "save|store|persist|flash|zero|home|calib" | sort -u | head -40
done