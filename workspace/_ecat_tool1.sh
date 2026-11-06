#!/bin/sh
EC=/usr/bin/ethercat
[ -x "$EC" ] || EC=/mnt/etherlab/bin/ethercat
echo "=== ethercat version ==="; $EC version 2>&1 | head -5
echo "=== master ==="; $EC master 2>&1 | head -30
echo "=== slaves ==="; $EC slaves 2>&1 | head -30
echo "=== domains ==="; $EC domains 2>&1 | head -80
