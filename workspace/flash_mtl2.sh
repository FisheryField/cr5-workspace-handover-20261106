L=/mToolServer/mToolServer.log
echo "=== A. exact JSON request body for singleFwAndXml ==="
grep -a -n -B25 "post /update/CR/singleFwAndXml" $L | tail -60
echo ""
echo "=== B. any 'no need to update' anywhere in the log? ==="
grep -a -c "no need to update" $L
grep -a -n "no need to update" $L | tail -5
echo ""
echo "=== C. every singleFwAndXml request in the log (with slaveId) ==="
grep -a -n "post /update/CR/singleFwAndXml\|starting update firmware of slave\|foe write result" $L
echo ""
echo "=== D. how is mToolServer started? (dobot.sh / rc / init) ==="
grep -rn "mToolServer" /dobot/bin/dobot.sh /etc/init.d/ /etc/rc.local 2>/dev/null | head -20
echo ""
echo "=== E. the port: search log for listen/port ==="
grep -a -n "port\|listen\|bind" $L | head -20
echo ""
echo "=== F. mToolServer version banner + start lines (head 40) ==="
head -40 $L
echo "=== DONE ==="
