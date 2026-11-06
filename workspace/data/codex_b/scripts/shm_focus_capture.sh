#!/bin/sh
# Focused high-rate read-only capture around changed shared-memory offsets.
TAG=${1:-shm_focus}
OUT=/tmp/$TAG
mkdir -p "$OUT"
PID=$(pidof codesyscontrol 2>/dev/null | awk '{print $1}')
[ -n "$PID" ] || { echo NO_PID; exit 2; }
echo "$PID" > "$OUT/pid"
date > "$OUT/start"
cat /proc/$PID/maps > "$OUT/maps"
# Main changing block: 0x73a84000, 512 KiB; secondary block: 0x73a41000, 128 KiB.
# Six other SysV segments: capture first page for presence/state correlation.
i=0
while [ "$i" -le 300 ]; do
  cat /proc/uptime >> "$OUT/times"
  dd if=/proc/$PID/mem of="$OUT/main_$i.bin" bs=4096 skip=473732 count=128 2>/dev/null
  dd if=/proc/$PID/mem of="$OUT/aux_$i.bin" bs=4096 skip=473665 count=32 2>/dev/null
  dd if=/proc/$PID/mem of="$OUT/s1_$i.bin" bs=4096 skip=430649 count=1 2>/dev/null
  dd if=/proc/$PID/mem of="$OUT/s2_$i.bin" bs=4096 skip=430795 count=1 2>/dev/null
  dd if=/proc/$PID/mem of="$OUT/s3_$i.bin" bs=4096 skip=432990 count=1 2>/dev/null
  dd if=/proc/$PID/mem of="$OUT/s4_$i.bin" bs=4096 skip=466285 count=1 2>/dev/null
  dd if=/proc/$PID/mem of="$OUT/s5_$i.bin" bs=4096 skip=468845 count=1 2>/dev/null
  dd if=/proc/$PID/mem of="$OUT/s6_$i.bin" bs=4096 skip=471405 count=1 2>/dev/null
  if [ "$i" -eq 0 ]; then
    echo READY_FOR_CALIBRATION
  fi
  i=$((i+1))
  sleep 0.1
done
date > "$OUT/end"
tar -czf "$OUT.tar.gz" -C /tmp "$TAG" 2>/dev/null
echo "DONE $OUT.tar.gz"
