#!/bin/sh

echo set pid affinity

ID=`ps -T|grep codesyscontrol|awk '{print $1}'`

echo $ID
echo "***********************************************"
for id in $ID
do
#./setaffinityxk $id 12
./setaffinityxk $id 2
done
echo "***********************************************"


