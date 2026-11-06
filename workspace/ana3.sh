cd /mnt/d/mydata/Workspace
arm-linux-gnueabihf-objdump -d -C -M force-thumb --start-address=0xf9520 --stop-address=0xf9c2c libdataSvr.so.bin > ue.asm 2>&1
arm-linux-gnueabihf-objdump -d -C -M force-thumb --start-address=0x1d9e90 --stop-address=0x1d9fe8 libdataSvr.so.bin > ue2.asm 2>&1
head -12 ue.asm
echo "=== UE calls ==="
grep -n "bl" ue.asm | head -80