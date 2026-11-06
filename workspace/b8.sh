chmod +x /tmp/amrd
echo "=== dump big kernel 0x0027d000 + 0x600000 ==="
/tmp/amrd 376 27d000 600000 raw > /tmp/kern.bin
ls -l /tmp/kern.bin; md5sum /tmp/kern.bin
echo "=== dump high range 0x73000000 + 0x3000000 ==="
/tmp/amrd 376 73000000 3000000 raw > /tmp/high.bin
ls -l /tmp/high.bin; md5sum /tmp/high.bin
echo "=== free space ==="
df -h /tmp | tail -1
echo "=== END ==="
