#!/bin/sh
# shm_zero_capture.sh —— 标零用「全量共享内存差分采集」（只读）
# 用法: shm_zero_capture.sh [TAG] [DURATION_SEC] [--full]
#   --full  除共享段外，再纳入非栈的可写匿名段

TAG="$1"; [ -n "$TAG" ] || TAG=zero_shm_$(date +%Y%m%d_%H%M%S)
DUR="$2"; [ -n "$DUR" ] || DUR=90
MODE="$3"

PID=$(pidof codesyscontrol 2>/dev/null | awk '{print $1}')
if [ -z "$PID" ]; then echo "NO_CODESYS_PID"; exit 2; fi

OUT=/tmp/$TAG
rm -rf "$OUT"
mkdir -p "$OUT/base" "$OUT/cur"
echo "$PID" > "$OUT/pid"
date > "$OUT/start"
cat /proc/$PID/maps > "$OUT/maps"

INCLUDE_ANON=0
[ "$MODE" = "--full" ] && INCLUDE_ANON=1

# ---------- 1) 收集区域：权限字段以 s/S 结尾 = 共享 ----------
N=0
: > "$OUT/regions.txt"
while read LINE; do
  [ -n "$LINE" ] || continue
  PERM=$(echo "$LINE" | awk '{print $2}')
  KEEP=0
  case "$PERM" in
    rw*s|rw*S) KEEP=1 ;;
  esac
  if [ "$KEEP" = "0" ] && [ "$INCLUDE_ANON" = "1" ]; then
    case "$PERM" in
      rw-p) KEEP=1 ;;
    esac
    case "$LINE" in
      *"[stack"*) KEEP=0 ;;
    esac
  fi
  [ "$KEEP" = "1" ] || continue
  RANGE=$(echo "$LINE" | awk '{print $1}')
  NAME=$(echo "$LINE" | awk '{print $6}')
  [ -n "$NAME" ] || NAME=anon
  AH=$(echo "$RANGE" | cut -d- -f1)
  BH=$(echo "$RANGE" | cut -d- -f2)
  AD=$((0x$AH)); BD=$((0x$BH)); SZ=$((BD-AD))
  [ "$SZ" -gt 0 ] || continue
  echo "$N $AH $BH $SZ $NAME" >> "$OUT/regions.txt"
  N=$((N+1))
done < /proc/$PID/maps

TOTAL=0
while read IDX AH BH SZ NAME; do TOTAL=$((TOTAL+SZ)); done < "$OUT/regions.txt"
echo "regions=$N total_bytes=$TOTAL pid=$PID" > "$OUT/summary.txt"

# 空间预检：需要 base + cur + firstchange 副本，约 3 倍总量 + 余量
FREE=$(df -k /tmp | awk 'NR==2 {print $4}')
NEED=$(( TOTAL/1024*3 + 30000 ))
if [ "$FREE" -lt "$NEED" ]; then
  echo "ERROR: /tmp 剩余 ${FREE}KB 不足（需要约 ${NEED}KB）—— 请先清理 /tmp"
  echo "提示: du -sk /tmp/* | sort -rn | head; 删除已归档的解包目录"
  exit 3
fi
echo "regions=$N bytes=$TOTAL free_kb=$FREE"
cat "$OUT/regions.txt"

# ---------- 2) 基线 ----------
while read IDX AH BH SZ NAME; do
  AD=$((0x$AH)); PG=$((AD/4096)); CN=$(( (SZ+4095)/4096 ))
  dd if=/proc/$PID/mem of="$OUT/base/R$IDX.bin" bs=4096 skip=$PG count=$CN 2>/dev/null
  cp "$OUT/base/R$IDX.bin" "$OUT/cur/R$IDX.bin" 2>/dev/null
done < "$OUT/regions.txt"
date > "$OUT/baseline_done"

# ---------- 3) 差分轮询 ----------
echo READY_FOR_CALIBRATION
END=$(( $(date +%s) + DUR ))
ROUND=0
while [ "$(date +%s)" -lt "$END" ]; do
  ROUND=$((ROUND+1))
  UP=$(awk '{print $1}' /proc/uptime)
  while read IDX AH BH SZ NAME; do
    AD=$((0x$AH)); PG=$((AD/4096)); CN=$(( (SZ+4095)/4096 ))
    dd if=/proc/$PID/mem of="$OUT/cur/R$IDX.bin" bs=4096 skip=$PG count=$CN 2>/dev/null
    cmp -l "$OUT/base/R$IDX.bin" "$OUT/cur/R$IDX.bin" 2>/dev/null | head -3000 > "$OUT/d.txt"
    CNT=$(wc -l < "$OUT/d.txt")
    if [ "$CNT" -gt 0 ]; then
      PAGES=$(awk '{p=int(($1-1)/4096); c[p]++} END{for (k in c) printf "%s:%d ", k, c[k]}' "$OUT/d.txt" | cut -c1-240)
      NP=$(awk '{p=int(($1-1)/4096); s[p]=1} END{print length(s)}' "$OUT/d.txt")
      FIRST=$(head -1 "$OUT/d.txt" | awk '{print $1}')
      LAST=$(tail -1 "$OUT/d.txt" | awk '{print $1}')
      echo "round=$ROUND t=$UP region=$IDX name=$NAME diffs=$CNT pages=$NP first=$FIRST last=$LAST" >> "$OUT/changes.txt"
      echo "    pages: $PAGES" >> "$OUT/changes.txt"
      if [ ! -f "$OUT/cur/R$IDX.firstchange.bin" ]; then
        cp "$OUT/cur/R$IDX.bin" "$OUT/cur/R$IDX.firstchange.bin"
        echo "    firstchange_at_round=$ROUND t=$UP" >> "$OUT/changes.txt"
      fi
    fi
  done < "$OUT/regions.txt"
  echo "$ROUND $UP" >> "$OUT/rounds.txt"
done

# ---------- 4) 收尾 ----------
date > "$OUT/end"
rm -f "$OUT/d.txt"
cd /tmp && tar -czf "/tmp/$TAG.tar.gz" "$TAG" 2>/dev/null
echo "DONE /tmp/$TAG.tar.gz"
ls -la "/tmp/$TAG.tar.gz"