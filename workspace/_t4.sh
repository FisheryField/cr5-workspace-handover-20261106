cd /opt/codesys/Platforms/Linux/Bin
./codesysload &
sleep 8
ps | grep -E 'codesys' | grep -v grep
netstat -lntp 2>/dev/null | grep 22000
