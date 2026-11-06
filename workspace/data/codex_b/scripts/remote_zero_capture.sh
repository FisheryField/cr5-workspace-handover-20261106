#!/bin/sh
# Read-only calibration capture for Dobot controller. Run as root.
set -u
TAG=${1:-zero_capture_$(date +%Y%m%d_%H%M%S)}
OUT=/tmp/$TAG
mkdir -p "$OUT"
echo "output=$OUT" > "$OUT/README"
date > "$OUT/start.time"
ps axww > "$OUT/ps.before"
for p in $(pidof codesyscontrol 2>/dev/null; pidof robot_control 2>/dev/null; pidof dobot 2>/dev/null); do
  [ -r /proc/$p/maps ] || continue
  echo "$p" >> "$OUT/pids"
  cat /proc/$p/cmdline | tr '\000' ' ' > "$OUT/pid_${p}.cmdline"
  cat /proc/$p/maps > "$OUT/pid_${p}.maps"
  cat /proc/$p/smaps > "$OUT/pid_${p}.smaps" 2>/dev/null || true
  # Raw pre-calibration snapshot of writable shared/anonymous mappings.
  awk '$2 ~ /^rw/ && ($6 == "" || $6 ~ /^\\[|^\/dev\\/shm/) {print $1, $2, $6}' "$OUT/pid_${p}.maps" > "$OUT/pid_${p}.regions"
  while read R P N; do
    A=${R%-*}; B=${R#*-}; ADEC=$(printf "%d" "0x$A"); BDEC=$(printf "%d" "0x$B"); S=$((BDEC-ADEC));
    [ "$S" -gt 0 ] || continue
    [ "$S" -le 33554432 ] || continue
    printf '%s %s %s\n' "$A" "$B" "$N" > "$OUT/pid_${p}_${A}.meta"
    dd if=/proc/$p/mem of="$OUT/pid_${p}_${A}.before.bin" bs=4096 skip=$((ADEC/4096)) count=$(((S+4095)/4096))  2>/dev/null || true
  done < "$OUT/pid_${p}.regions"
done
# System-call trace for the calibration commit path.
for p in $(cat "$OUT/pids" 2>/dev/null); do
  strace -ff -ttt -xx -e trace=open,openat,write,pwrite64,rename,fsync,fdatasync -p "$p" -o "$OUT/strace_${p}" 2>/dev/null & echo $! >> "$OUT/strace.pids"
done
# EtherCAT raw capture if tcpdump is present.
if command -v tcpdump >/dev/null 2>&1; then
  tcpdump -i any -s 0 -B 4096 -w "$OUT/ethercat.pcap" ether proto 0x88a4 >/dev/null 2>"$OUT/tcpdump.err" & echo $! > "$OUT/tcpdump.pid"
fi
# Poll process maps and controller log timestamps while the user performs one calibration.
: > "$OUT/events.log"
for i in $(seq 1 600); do
  T=$(date +%s.%N)
  echo "=== $T ===" >> "$OUT/events.log"
  for p in $(cat "$OUT/pids" 2>/dev/null); do
    [ -r /proc/$p/status ] && awk '/State|VmRSS|Threads/ {print}' /proc/$p/status >> "$OUT/events.log"
  done
  sleep 0.1
done
# Stop tracers and make post snapshots.
for x in $(cat "$OUT/strace.pids" 2>/dev/null); do kill "$x" 2>/dev/null || true; done
[ -s "$OUT/tcpdump.pid" ] && kill "$(cat "$OUT/tcpdump.pid")" 2>/dev/null || true
for p in $(cat "$OUT/pids" 2>/dev/null); do
  [ -r /proc/$p/maps ] || continue
  cat /proc/$p/maps > "$OUT/pid_${p}.maps.after"
  while read R P N; do
    A=${R%-*}; B=${R#*-}; ADEC=$(printf "%d" "0x$A"); BDEC=$(printf "%d" "0x$B"); S=$((BDEC-ADEC));
    [ "$S" -gt 0 ] && [ "$S" -le 33554432 ] || continue
    dd if=/proc/$p/mem of="$OUT/pid_${p}_${A}.after.bin" bs=4096 skip=$((ADEC/4096)) count=$(((S+4095)/4096))  2>/dev/null || true
  done < "$OUT/pid_${p}.regions"
done
date > "$OUT/end.time"
ps axww > "$OUT/ps.after"
# Compress raw snapshots for transfer.
tar -czf "$OUT.tar.gz" -C /tmp "$(basename "$OUT")" 2>/dev/null || true
echo "$OUT"

