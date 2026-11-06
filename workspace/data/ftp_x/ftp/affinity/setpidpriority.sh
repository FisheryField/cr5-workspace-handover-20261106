#!/bin/sh

echo set pid affinity

ID=`lsof :1217|grep codesyscontrol|awk '{print $1}'`

echo $ID
echo "***********************************************"
for id in $ID
do
./setaffinityxk $id 3
done
echo "***********************************************"
