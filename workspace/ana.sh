cd /mnt/d/mydata/Workspace
which arm-linux-gnueabihf-objdump arm-linux-gnueabihf-readelf
echo "--- strings (file offsets) ---"
strings -t x libdataSvr.so.bin | grep -E "homeEncoder|innerEncoder|jointHomeState|outEncoder|Encoder"
echo "--- symbols ---"
arm-linux-gnueabihf-readelf -sW libdataSvr.so.bin | grep -i -E "updateEncoderData|JsonFile|Encoder" | head -30
echo "--- sections ---"
arm-linux-gnueabihf-readelf -SW libdataSvr.so.bin | grep -E "\.rodata|\.text|\.data|\.bss"