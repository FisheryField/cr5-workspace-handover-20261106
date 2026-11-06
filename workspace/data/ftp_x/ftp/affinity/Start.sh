#!/bin/sh

./affinity.sh 4 

./setthreadaffinity.sh 

./setthreadpriority.sh

#kexec -d -p /opt/codesys/uImage --dtb /opt/codesys/imx6q-sabresd.dtb --command-line="noinitrd console=ttymxc0,115200 root=/dev/mmcblk3p1 rootwait rw init=/linuxrc nosmp"