#!/bin/sh
touch /tmp/ab_stop
sleep 1
ps | grep -c 'ab_sample.sh' 
rm -f /tmp/ab_stop
echo "stopped old"
