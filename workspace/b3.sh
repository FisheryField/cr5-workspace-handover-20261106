echo "=== read 0x10000 from 0x75a9a000 ==="
dd if=/proc/376/mem bs=1 skip=$((0x75a9a000)) count=$((0x10000)) 2>/dev/null | od -An -tx1 -v | tr -d ' \n' > /tmp/mem_75a9a000.hex
wc -c /tmp/mem_75a9a000.hex
echo "=== first 512 bytes of that region ==="
dd if=/proc/376/mem bs=1 skip=$((0x75a9a000)) count=512 2>/dev/null | od -An -tx1 -v
echo "=== read stack:383 region header ==="
dd if=/proc/376/mem bs=1 skip=$((0x75a76000)) count=256 2>/dev/null | od -An -tx1 -v
echo "=== search ASCII 'CODESYS' / 'Application' / 'IoConfig' ASCII (not utf16) in the region 0x75a76000-0x75cb8000 ==="
dd if=/proc/376/mem bs=4096 skip=$((0x75a76000/4096)) count=$((0x240000/4096)) 2>/dev/null > /tmp/stack383.bin
ls -l /tmp/stack383.bin
echo "--- grep -abo flags ---"
grep -abo 'Application' /tmp/stack383.bin | head -20
echo "--- IoConfig ---"
grep -abo 'IoConfig' /tmp/stack383.bin | head -20
echo "--- a1.config ---"
grep -abo 'a1.config' /tmp/stack383.bin | head -20
echo "--- CODESYS ---"
grep -abo 'CODESYS' /tmp/stack383.bin | head -10
echo "--- readable strings sample (first 30 lines of length>=8) ---"
strings -n 8 /tmp/stack383.bin 2>/dev/null | head -30
echo "=== END ==="
