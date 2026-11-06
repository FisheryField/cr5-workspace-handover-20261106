echo "=== find files named *calib* / *zero* ==="
find / -path /proc -prune -o -path /sys -prune -o -path /dobot/userdata/project/logs -prune -o -type f \( -iname "*calib*" -o -iname "*zero*" \) -print 2>/dev/null | head -50
echo "=== Recipe files ==="
for f in /home/ftp/PlcLogic/Recipe/SaveAxesValue.AxesValues.txtrecipe /home/ftp/PlcLogic/Recipe/SavePos.txt /home/ftp/PlcLogic/Recipe/SlaveInfos.SlaveInfos.txtrecipe /home/ftp/PlcLogic/Recipe/Update.txt; do echo "--- $f ---"; cat "$f" 2>/dev/null; echo; done
echo "=== sixForce params ==="
for f in caliParams.json config.json switch.json; do echo "--- $f ---"; cat /dobot/userdata/project/process/sixForce/$f 2>/dev/null; echo; done
echo "=== vision_calibrate.json ==="
head -c 700 /dobot/userdata/project/process/vision_calibrate.json 2>/dev/null
echo "=== Application.app GVL symbols ==="
strings /home/ftp/PlcLogic/Application/Application.app 2>/dev/null | grep -oE "GVL\.[A-Za-z_0-9]+" | sort -u | head -60
echo "=== Application.app calib/zero symbols ==="
strings /home/ftp/PlcLogic/Application/Application.app 2>/dev/null | grep -iE "zeroOffset|EncoderZero|ZeroCalib|SetZero|HomeOffset|Calibr" | sort -u | head -40
echo "=== gcontrol zero-ish paths ==="
strings /dobot/bin/gcontrol 2>/dev/null | grep -E "/dobot/userdata|\.json|\.bin" | grep -iE "zero|calib|param|encode|axis|offset" | sort -u | head -40