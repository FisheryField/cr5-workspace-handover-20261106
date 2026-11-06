echo "=== gcontrol: SDO / CoE / 0x607C / 0x1010 ==="
strings /dobot/bin/gcontrol 2>/dev/null | grep -iE "sdo|coe|607c|0x1010|1010|store param|save param|homeoffset|home offset|encoder" | sort -u | head -40
echo "=== libCmpDobot6Axes.so ==="
strings /home/ftp/.lib/libCmpDobot6Axes.so 2>/dev/null | grep -iE "sdo|coe|607c|1010|store|home|zero|encoder|offset|param" | sort -u | head -50
echo "=== libIoDrvDobIO.so ==="
strings /home/ftp/.lib/libIoDrvDobIO.so 2>/dev/null | grep -iE "sdo|coe|607c|1010|store|home|zero|encoder|offset" | sort -u | head -30
echo "=== .lib 目录 ==="
ls -la /home/ftp/.lib/
echo "=== /opt/codesys 平台库 ==="
ls -la /opt/codesys/Platforms/Linux/Bin/
echo "=== gcontrol 里的 HOMEParams 相关 ==="
strings /dobot/bin/gcontrol 2>/dev/null | grep -iE "homeparam|home_cmd|HOMECmd|setHome|SetHOME" | sort -u | head -20