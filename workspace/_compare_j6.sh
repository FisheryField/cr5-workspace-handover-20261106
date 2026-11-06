LOG=/dobot/userdata/CR5_sys_files/project/logs/all/log
echo "=== 版本确认 ==="
curl -s -X POST http://127.0.0.1:22000/settings/version 2>/dev/null | tr -d ' \t' | grep -E "servo[1-6]"
echo
echo "=== J6 当时的刷写记录（固件部分）==="
grep -a -E "start FoE write|updateSlaveFW|firmware|success" /mToolServer/mToolServer.log 2>/dev/null | tail -12
echo
echo "=== 停止应用栈 ==="
for p in $(pidof codesyscontrol); do kill $p; done
for p in $(pidof gcontrol); do kill $p; done
sleep 6
ps | grep -E "codesys|gcontrol" | grep -v grep || echo "已停止"
chmod +x /tmp/ecat_zero

echo
echo "###### slave 8 (J6, 已是 3.2.D.8) ######"
echo -n "  0x6064:00 实际位置         "; /tmp/ecat_zero rv 8 0x6064 0 | tail -1
echo -n "  0x5000:01 厂商模拟量        "; /tmp/ecat_zero rv 8 0x5000 1 | tail -1
for a in "0x2000 1" "0x2001 14" "0x2001 18" "0x2001 19" "0x200C 3" "0x200D 8" "0x200D 9"; do
  set -- $a
  echo -n "  $1:$2 "; /tmp/ecat_zero rv 8 $1 $2 | tail -1
done

echo
echo "###### slave 7 (J5, 仍是 3.1.5.0) —— 同总线对照组 ######"
echo -n "  0x6064:00 实际位置         "; /tmp/ecat_zero rv 7 0x6064 0 | tail -1
echo -n "  0x5000:01 厂商模拟量        "; /tmp/ecat_zero rv 7 0x5000 1 | tail -1
for a in "0x2000 1" "0x2001 14" "0x2001 18" "0x2001 19" "0x200C 3" "0x200D 8" "0x200D 9"; do
  set -- $a
  echo -n "  $1:$2 "; /tmp/ecat_zero rv 7 $1 $2 | tail -1
done

echo
echo "=== DONE ==="; date
