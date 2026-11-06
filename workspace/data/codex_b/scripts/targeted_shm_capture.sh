#!/bin/sh
# Targeted read-only SysV shared-memory capture for CODESYS calibration.
set -u
TAG=${1:-shm_capture_$(date +%Y%m%d_%H%M%S)}
OUT=/tmp/$TAG
mkdir -p "$OUT/snap"
PID=$(pidof codesyscontrol 2>/dev/null | awk '{print $1}')
[ -n "$PID" ] || { echo NO_CODESYS_PID; exit 2; }
echo "$PID" > "$OUT/pid"
cat /proc/$PID/maps > "$OUT/maps.before"
date > "$OUT/start"
# Known shared-memory regions from the current controller map.
# start address, size in bytes, label
REGIONS="73a00000 a00000 shm_73a00000
69239000 92000 shm_69239000
692cb000 92000 shm_692cb000
69b5e000 92000 shm_69b5e000
71d6d000 92000 shm_71d6d000
7276d000 92000 shm_7276d000
7316d000 92000 shm_7316d000"
# Convert a hexadecimal string to decimal using POSIX shell arithmetic.
read_region() {
  A=$1; S=$2; F=$3
  AD=$((0x$A)); SD=$((0x$S));
  dd if=/proc/$PID/mem of="$F" bs=4096 skip=$((AD/4096)) count=$(((SD+4095)/4096)) 2>/dev/null
}
hash_region() {
  A=$1; S=$2
  AD=$((0x$A)); SD=$((0x$S));
  dd if=/proc/$PID/mem bs=4096 skip=$((AD/4096)) count=$(((SD+4095)/4096)) 2>/dev/null | md5sum | awk '{print $1}'
}
# Baseline snapshots and hashes.
echo "$REGIONS" > "$OUT/regions"
set -- $REGIONS
while [ $# -ge 3 ]; do
  A=$1; S=$2; N=$3; shift 3
  read_region "$A" "$S" "$OUT/snap/${N}.before.bin"
  hash_region "$A" "$S" > "$OUT/${N}.hash"
done
echo READY_FOR_CALIBRATION
# Poll for 60 seconds; save a full region only on hash change.
for i in $(seq 1 600); do
  T=$(date +%s)
  set -- $REGIONS
  while [ $# -ge 3 ]; do
    A=$1; S=$2; N=$3; shift 3
    H=$(hash_region "$A" "$S")
    OLD=$(cat "$OUT/${N}.hash" 2>/dev/null || true)
    if [ "$H" != "$OLD" ] && [ -n "$H" ]; then
      read_region "$A" "$S" "$OUT/snap/${N}.${T}.${i}.bin"
      echo "$T $i $N $OLD $H" >> "$OUT/changes.log"
      echo "$H" > "$OUT/${N}.hash"
    fi
  done
  sleep 0.1
done
date > "$OUT/end"
cat /proc/$PID/maps > "$OUT/maps.after" 2>/dev/null || true
tar -czf "$OUT.tar.gz" -C /tmp "$(basename "$OUT")" 2>/dev/null || true
echo "DONE $OUT.tar.gz"

