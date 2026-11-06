
#!/bin/sh


#Marco Value
num=1
num1=1
pid=0
PRIOBak=-1

echo set CoDeSys thread affinity

ID=`ps -eTf|grep EtherCAT_Task|awk '{print $1}'`


echo "**************************************************"
echo "ThreadIDs from MainTask:"
echo $ID

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
