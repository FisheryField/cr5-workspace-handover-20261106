V32="/mnt/d/software/DobotStudio/V1.3.4-stable/V1.3.4-stable/upgradeFiles/3.5.6/3.5.6.1/files/CR5_Servo_ST_FOE_V3.2.D.8.bin"
V315="/mnt/d/mydata/working things/机械臂控制柜数据/3.1.5_candidate_upgrade/CR5_Servo_ST_FOE_V3.1.5.0_UNVERIFIED.bin"
ls -la "$V32" "$V315" 2>&1
for f in "$V32" "$V315"; do echo "##### $f"; strings -n 4 "$f" | wc -l; strings -n 4 "$f" | grep -i -E "3\.[0-9]\.[0-9A-F]|version|V[0-9]\.[0-9]" | head -12; echo "-- 存储/参数相关 --"; strings -n 4 "$f" | grep -i -E "store|eeprom|save|flash|param|cali|home|encoder" | head -20; done
echo "=== strings 差异 (V3.2.D.8 独有) ==="
strings -n 5 "$V32" | sort -u > /tmp/s32.txt; strings -n 5 "$V315" | sort -u > /tmp/s315.txt
comm -23 /tmp/s32.txt /tmp/s315.txt | head -60
echo "=== 共有/数量 ==="; wc -l /tmp/s32.txt /tmp/s315.txt