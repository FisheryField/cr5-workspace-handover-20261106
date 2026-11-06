echo '=== loadParams.json 内容 ==='
cat /dobot/userdata/project/settings/function/loadParams.json 2>/dev/null; echo
echo '=== 它现在的时间戳 ==='
ls -la /dobot/userdata/project/settings/function/loadParams.json
echo
echo '=== 库里谁在写 loadParams ==='
strings /dobot/bin/lib/libdataSvr.so.1.0.0 2>/dev/null | grep -i "loadparam" | head -10
echo
echo '=== 对照组：另一个改过的文件 SavePos.txt ==='
cat /home/ftp/PlcLogic/Recipe/SavePos.txt 2>/dev/null | od -A d -t x1 | head -8
echo
echo '=== 当前 homeEncoder.json 末条 ==='
tail -20 /dobot/userdata/project/settings/function/homeEncoder.json
