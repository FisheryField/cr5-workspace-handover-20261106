echo "=== SavePos.txt 两种 dump ==="
od -An -tx1 /home/ftp/PlcLogic/Recipe/SavePos.txt
echo "--- as text ---"
cat /home/ftp/PlcLogic/Recipe/SavePos.txt; echo
echo "--- overTurn ---"
od -An -tx1 /mToolServer/overTurn/SavePos.txt
cat /mToolServer/overTurn/SavePos.txt; echo
echo "=== Update.txt ---"
od -An -tx1 /home/ftp/PlcLogic/Recipe/Update.txt
echo "=== libdataSvr 大小/符号 ==="
ls -la /dobot/bin/lib/libdataSvr.so.1.0.0
echo "=== 拷贝到 /tmp 供 scp ==="
cp /dobot/bin/lib/libdataSvr.so.1.0.0 /tmp/libdataSvr.so.bin && ls -la /tmp/libdataSvr.so.bin