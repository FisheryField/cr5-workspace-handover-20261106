echo ===DBSTART===
cat /etc/init.d/dbStart.sh
echo ===RCS===
grep -n codesys /etc/init.d/rcS 2>/dev/null
echo ===PROCS===
for p in /proc/[0-9]*; do
  c=$(tr '\0' ' ' < $p/cmdline 2>/dev/null | head -c 80)
  [ -n "$c" ] && echo "$p $c"
done | grep -i -E 'codesys|watch|monitor|guard|keep'
echo ===CRON===
crontab -l 2>/dev/null
ls /etc/cron* 2>/dev/null
