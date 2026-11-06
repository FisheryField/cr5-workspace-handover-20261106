#!/bin/sh
echo "=== codesyscontrol pid $(pidof codesyscontrol) 全部 rw 区 ==="
grep -E ' rw' /proc/$(pidof codesyscontrol)/maps
echo
echo "=== gcontrol pid $(pidof gcontrol) 全部 rw 区 ==="
grep -E ' rw' /proc/$(pidof gcontrol)/maps
