L=/mToolServer/mToolServer.log
echo "=== SAVE POSE LINES"; grep -an "SavePose\|SavePos\|Joint1" $L | head -40
echo "=== FLASH SEQUENCE"; grep -an "updateSlaveFW()#246\|createUpdateThd()#97\|foe write result" $L | tail -30
echo "=== ZERO/HOME/CALIB STRINGS IN LOG"; grep -ain "zero\|home\|calib\|deviat\|alarm" $L | head -30
echo "=== LOG HEAD"; head -25 $L
echo "=== LOG SIZE/LINES"; wc -l $L
echo "=== BIN STRINGS"; strings -n 6 /mToolServer/mToolServer | grep -i "pose\|zero\|home\|calib\|joint" | head -60
echo "=== DONE"