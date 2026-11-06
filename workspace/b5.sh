chmod +x /tmp/amrd /tmp/amdump
echo "=== inline hex of suspected code region ==="
/tmp/amrd 376 75a8f000 200 hex
echo "=== where does the 24-byte Device.Application fingerprint live (utf16)? ==="
echo "=== dump whole stack:383 region to /tmp (raw) ==="
/tmp/amrd 376 75a76000 240000 > /tmp/reg383.bin
ls -l /tmp/reg383.bin
md5sum /tmp/reg383.bin
echo "=== END ==="
