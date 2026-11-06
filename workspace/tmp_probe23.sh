echo "=== R routes in mToolServer"
strings -n 4 /mToolServer/mToolServer | grep "^/" | sort -u | head -60
echo "=== R all http-ish tokens"
strings -n 5 /mToolServer/mToolServer | grep -i "update/\|protocol/\|/CR/\|zero\|home\|calib\|unlock\|offset" | sort -u | head -60
echo "=== R DONE"