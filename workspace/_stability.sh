PID=$(pidof codesyscontrol | awk '{print $1}')
SEL=$(grep "SYSVe901001b" /proc/$PID/maps | head -1)
B=$((0x$(echo "$SEL" | cut -d- -f1)))
echo "pid=$PID base=0x$(printf %x $B) uptime=$(cat /proc/uptime)"
rm -rf /tmp/stab
mkdir -p /tmp/stab
echo "$B" > /tmp/stab/base.txt
N=1
while [ $N -le 6 ]; do
  cat /proc/uptime > /tmp/stab/t${N}.time
  dd if=/proc/$PID/mem of=/tmp/stab/p132_${N}.bin bs=4096 skip=$((B/4096+132)) count=1 2>/dev/null
  dd if=/proc/$PID/mem of=/tmp/stab/p133_${N}.bin bs=4096 skip=$((B/4096+133)) count=1 2>/dev/null
  dd if=/proc/$PID/mem of=/tmp/stab/pose_${N}.bin bs=1 skip=$((B+133*4096+4)) count=24 2>/dev/null
  echo "  round $N"
  N=$((N+1))
  sleep 3
done
ls -la /tmp/stab/
cd /tmp && tar -czf /tmp/stab.tar.gz stab 2>/dev/null
echo "tar:"; ls -la /tmp/stab.tar.gz
