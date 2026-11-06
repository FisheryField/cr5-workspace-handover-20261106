#!/bin/sh


echo start set smp_affinity

echo $1 >/proc/irq/288/smp_affinity 

echo set smp_affinity stop
