chmod +x /tmp/amrd
echo "=== raw dump of region 0x75a76000..0x75cb8000 ==="
/tmp/amrd 376 75a76000 241000 raw > /tmp/reg383.bin
ls -l /tmp/reg383.bin
md5sum /tmp/reg383.bin
echo "=== also dump 0x0027d000..0x0036b000 (the rwxp anon the handover flagged) ==="
/tmp/amrd 376 27d000 ee000 raw > /tmp/reg27d.bin
ls -l /tmp/reg27d.bin
echo "=== hex head of region at 0x75a90000 ==="
/tmp/amrd 376 75a90000 100 hex
echo "=== END ==="
