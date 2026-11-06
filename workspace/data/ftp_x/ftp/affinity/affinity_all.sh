#!/bin/sh


###需要处理的外设中断，主要有serial --> CPU1
###							 	usb --> CPU0
###						   ethernet --> CPU2
###						   

ID=`cat /proc/interrupts |grep ethernet |sort | cut -c 0-3`

echo set ethernet irq affinity
for id in $ID
do
	echo 4 >/proc/irq/$id/smp_affinity 
done
echo set ethernet irq affinity success
sleep 1

ID=`cat /proc/interrupts |grep serial |sort | cut -c 0-3`

echo set serial irq affinity
for id in $ID
do
	echo 2 >/proc/irq/$id/smp_affinity 
done
echo set serial irq affinity success
sleep 1


ID=`cat /proc/interrupts |grep usb |sort | cut -c 0-3`

echo set usb irq affinity
for id in $ID
do
	echo 1 >/proc/irq/$id/smp_affinity 
done
echo set usb irq affinity success
sleep 1