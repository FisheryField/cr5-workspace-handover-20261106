#!/bin/sh
# BusyBox-compatible, read-only targeted shared-memory capture.
TAG=${1:-shm_capture}
OUT=/tmp/$TAG
mkdir -p "$OUT/snap"
PID=$(pidof codesyscontrol 2>/dev/null | awk '{print $1}')
if [ -z "$PID" ]; then echo NO_CODESYS_PID; exit 2; fi
echo "$PID" > "$OUT/pid"
cat /proc/$PID/maps > "$OUT/maps.before"
date > "$OUT/start"
# name skip-pages count-pages
capture() {
  N=$1; K=$2; C=$3
  dd if=/proc/$PID/mem of="$OUT/snap/$N.before.bin" bs=4096 skip=$K count=$C 2>/dev/null
  dd if=/proc/$PID/mem bs=4096 skip=$K count=$C 2>/dev/null | md5sum | awk '{print $1}' > "$OUT/$N.hash"
}
check() {
  N=$1; K=$2; C=$3; T=$4; I=$5
  H=$(dd if=/proc/$PID/mem bs=4096 skip=$K count=$C 2>/dev/null | md5sum | awk '{print $1}')
  O=$(cat "$OUT/$N.hash" 2>/dev/null)
  if [ -n "$H" ] && [ "$H" != "$O" ]; then
    dd if=/proc/$PID/mem of="$OUT/snap/$N.$T.$I.bin" bs=4096 skip=$K count=$C 2>/dev/null
    echo "$T $I $N $O $H" >> "$OUT/changes.log"
    echo "$H" > "$OUT/$N.hash"
  fi
}
# 73a00000-74400000, 10 MiB
capture shm_73a00000 473600 2560
# Six 0x92000 SysV regions
capture shm_69239000 430649 146
capture shm_692cb000 430795 146
capture shm_69b5e000 432990 146
capture shm_71d6d000 466285 146
capture shm_7276d000 468845 146
capture shm_7316d000 471405 146
echo READY_FOR_CALIBRATION
I=1
while [ "$I" -le 300 ]; do
  T=$(date +%s)
  check shm_73a00000 473600 2560 "$T" "$I"
  check shm_69239000 430649 146 "$T" "$I"
  check shm_692cb000 430795 146 "$T" "$I"
  check shm_69b5e000 432990 146 "$T" "$I"
  check shm_71d6d000 466285 146 "$T" "$I"
  check shm_7276d000 468845 146 "$T" "$I"
  check shm_7316d000 471405 146 "$T" "$I"
  I=$((I+1))
  sleep 0.2
done
date > "$OUT/end"
cat /proc/$PID/maps > "$OUT/maps.after" 2>/dev/null
tar -czf "$OUT.tar.gz" -C /tmp "$TAG" 2>/dev/null
echo "DONE $OUT.tar.gz"
