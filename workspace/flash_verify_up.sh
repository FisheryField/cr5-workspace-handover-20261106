echo "=== uploaded file ==="
ls -la /tmp/tUpdate/slave/
echo ""
echo "=== size + md5 + sha256 ==="
F=/tmp/tUpdate/slave/CR5_Servo_ST_FOE_V3.1.5.0_PATCHED_no_correction.bin
wc -c < $F
md5sum $F
sha256sum $F 2>/dev/null || echo "(no sha256sum)"
echo ""
echo "=== first 32 bytes (package header) ==="
od -A x -t x1 -N 32 $F
echo ""
echo "=== the 6 patched bytes at payload offset 0x14AFE (= file offset 0x14B1E) ==="
echo "expect: 01 46 00 bf 00 bf"
dd if=$F bs=1 skip=$((0x14B1E)) count=6 2>/dev/null | od -A x -t x1
echo ""
echo "=== DONE ==="
