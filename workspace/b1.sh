echo "=== date/uptime ==="; date; uptime
echo "=== codesyscontrol pid ==="
for p in /proc/[0-9]*; do
  n=$(cat $p/comm 2>/dev/null)
  case "$n" in
    codesyscontrol*) echo "PID=${p#/proc/} comm=$n";;
  esac
done
echo "=== Application.app on disk ==="
find / -name 'Application.app' -not -path '/proc/*' 2>/dev/null | while read f; do
  echo "$f  size=$(wc -c < $f)"
  ls -l "$f"
  md5sum "$f"
done
echo "=== maps (codesyscontrol) ==="
PID=$(for p in /proc/[0-9]*; do n=$(cat $p/comm 2>/dev/null); case "$n" in codesyscontrol*) echo ${p#/proc/};; esac; done | head -1)
echo "PID=$PID"
if [ -n "$PID" ]; then
  echo "--- maps count: $(wc -l < /proc/$PID/maps)"
  cat /proc/$PID/maps
fi
echo "=== END ==="
