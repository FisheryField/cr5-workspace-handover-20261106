L=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "=== nEncoderChannel ==="
grep -a -o -iE ".{0,40}nEncoderChannel.{0,40}" $L | tail -10
echo
echo "=== 19:27:04 前后 60 行 ==="
sed -n "379270,379330p" $L
echo
echo "=== 各二进制里的 offset/zero 符号 ==="
for f in /dobot/bin/gcontrol /dobot/bin/lib/libdataSvr.so.1.0.0 /usr/lib/libCmpDobot6Axes.so; do
  echo "##### $f"
  strings $f | grep -i -E "positionoffset|homeoffset|setzero|zerooffset|homeflag|setencodercnt|encoder ?cnt|setHome|SetZero" | head -15
done
echo "##### Application.app"
strings /home/ftp/PlcLogic/Application/Application.app | grep -i -E "homeEncoder|rt_AxisPos|SaveAxesValue|AxisOffset|HomeOffset|Offset" | head -20
echo "=== libCmpDobot6Axes 符号 ==="
nm -D /usr/lib/libCmpDobot6Axes.so 2>/dev/null | head -30 || strings /usr/lib/libCmpDobot6Axes.so | grep -i -E "home|offset|zero" | head -30