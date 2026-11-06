for f in /dobot/bin/gcontrol /dobot/bin/lib/libdataSvr.so.1.0.0 /dobot/bin/lib/libdataSvrPlugin.so.1.0.0 /usr/lib/libCmpDobot6Axes.so /home/ftp/.lib/libCmpDobot6Axes.so; do
  echo "########## $f ##########"
  strings "$f" 2>/dev/null | grep -iE "calibrate|homeparam|homecmd|tagHOME|/home|goHome|zero|SetEnc" | sort -u | head -25
done
echo "=== libdataSvr 里所有 /xxx 形式路由（前 60）==="
strings /dobot/bin/lib/libdataSvr.so.1.0.0 2>/dev/null | grep -E "^/" | grep -vE "^\.\.|/home/|/usr/|/opt/|/lib|/etc|/dev|/proc|/sys" | sort -u | head -60