#!/bin/sh
# zeroprobe.sh —— 采集"零点/编码器状态指纹"（只读）
# 用法: zeroprobe.sh [TAG]
TAG="$1"
if [ -z "$TAG" ]; then TAG=zeroprobe_$(date +%Y%m%d_%H%M%S); fi
OUT=/tmp/$TAG
rm -rf "$OUT"
mkdir -p "$OUT"

# ---------- 1) 状态指纹 ----------
{
  echo "== date / uptime =="
  date
  cat /proc/uptime
  echo
  echo "== 控制器/伺服版本 =="
  wget -qO- --post-data='' http://127.0.0.1:22000/settings/version 2>/dev/null || echo "(version 接口不可用)"
  echo
  echo "== homeEncoder.json =="
  cat /dobot/userdata/project/settings/function/homeEncoder.json 2>/dev/null
  echo
  echo "== 进程 =="
  ps | grep -E "codesyscontrol|gcontrol" | grep -v grep
  echo
} > "$OUT/state.txt" 2>&1

PID=$(pidof codesyscontrol 2>/dev/null | awk '{print $1}')
if [ -z "$PID" ]; then
  echo "NO_CODESYS_PID" >> "$OUT/state.txt"
  cd /tmp && tar -czf "/tmp/$TAG.tar.gz" "$TAG" 2>/dev/null
  echo "DONE_NO_PID /tmp/$TAG.tar.gz"
  exit 2
fi
echo "pid=$PID" >> "$OUT/state.txt"
cp /proc/$PID/maps "$OUT/maps.txt"

# ---------- 2) 10MB 段：按 key 名定位，不写死地址 ----------
SEL=$(grep "SYSVe901001b" /proc/$PID/maps 2>/dev/null | head -1)
if [ -z "$SEL" ]; then
  echo "SYSVe901001b: NOT FOUND" >> "$OUT/state.txt"
else
  echo "10MB segment: $SEL" >> "$OUT/state.txt"
  BASE=$(echo "$SEL" | cut -d- -f1)
  END=$(echo "$SEL" | cut -d- -f2 | cut -d' ' -f1)
  BAD=$((0x$BASE)); EAD=$((0x$END))
  PG=$((BAD/4096)); NP=$(( (EAD-BAD)/4096 ))
  echo "base_hex=$BASE base_dec=$BAD pages=$NP" >> "$OUT/state.txt"
  dd if=/proc/$PID/mem of="$OUT/seg_full.bin" bs=4096 skip=$PG count=$NP 2>/dev/null
  for p in 64 65 132 133; do
    dd if=/proc/$PID/mem of="$OUT/page_$p.bin" bs=4096 skip=$((PG+p)) count=1 2>/dev/null
  done
  {
    echo
    echo "== 关键页 0xE20 起 64 字节（od -t x4，小端）=="
    for p in 64 132; do
      echo "--- page $p ---"
      dd if="$OUT/page_$p.bin" bs=1 skip=3616 count=64 2>/dev/null | od -A d -t x4
    done
  } >> "$OUT/state.txt"
fi

# ---------- 3) 另外几个 584KB 段也存一份 ----------
for K in SYSV16039711 SYSV13039711 SYSV18039711 SYSV0b039711; do
  L=$(grep "$K" /proc/$PID/maps 2>/dev/null | head -1)
  [ -n "$L" ] || continue
  B=$(echo "$L" | cut -d- -f1)
  E=$(echo "$L" | cut -d- -f2 | cut -d' ' -f1)
  BD=$((0x$B)); ED=$((0x$E)); PP=$((BD/4096)); NN=$(( (ED-BD)/4096 ))
  dd if=/proc/$PID/mem of="$OUT/seg_$K.bin" bs=4096 skip=$PP count=$NN 2>/dev/null
done

cd /tmp && tar -czf "/tmp/$TAG.tar.gz" "$TAG" 2>/dev/null
echo "DONE /tmp/$TAG.tar.gz"
ls -la "/tmp/$TAG.tar.gz"
df -h /tmp | tail -1
