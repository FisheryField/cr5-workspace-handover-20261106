cd /mnt/d/mydata/Workspace
arm-linux-gnueabihf-objdump -d -C --start-address=0xf9521 --stop-address=0xf9c2d libdataSvr.so.bin > ue.asm 2>&1
arm-linux-gnueabihf-objdump -d -C --start-address=0x1d9e91 --stop-address=0x1d9fe9 libdataSvr.so.bin > ue2.asm 2>&1
wc -l ue.asm ue2.asm
echo "=== UE: 调用 (bl) ==="
grep -n -E "\tbl\t" ue.asm | head -80
echo "=== UE: 引用 rodata 常量 ==="
grep -n -E "20e3[0-9a-f][0-9a-f]|20e9|20ea" ue.asm | head -40