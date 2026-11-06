
#!/bin/sh


#Marco Value
num=1
num1=1
pid=0
PRIOBak=-1

echo set CoDeSys thread affinity

ID=`ps -eTf|grep EtherCAT_Task|awk '{print $1}'`
ID1=`ps -eTf|grep codesyscontrol|awk '{print $1}'`
ID2=`ps -eTf|grep gcontrol|awk '{printk $1}'`

echo "**************************************************"
echo "ThreadIDs from MainTask:"
echo $ID
echo $ID1
echo $ID2

for id in $ID1
do
pid=${id}
./AffinitySetup $pid 3
done

for id in $ID2
do
pid=${id}
./AffinitySetup $pid 3
done

for id in $ID
do
pid=${id}
./AffinitySetup $pid 3
done

for id in $ID
do
#echo $num
if [ "${num}" = "${num1}" ] ;then
pid=${id}
echo "PID from MainTask:"
echo $pid
num=2
#echo $num
fi

./AffinitySetup $pid 2

done
