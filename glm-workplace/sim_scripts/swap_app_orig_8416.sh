#!/bin/sh
# swap_app_orig_8416.sh - ACTIVATE ORIGINAL main app 8416cf0e for homing under 3.1.5.0
# Approved by user. Steps:
#   1. backup current allST (patched 9a808cd9) to BACKUP_prehome_swap_<ts>
#   2. copy BACKUP_ORIGINAL Application.app + .crc into allST (temp+mv, atomic)
#   3. verify md5 == 8416cf0eee070a640702c077eb904b4e
#   4. sync + reboot
set -e
CS=/dobot/userdata/codesys
TS=$(date +%Y%m%d_%H%M%S)

echo "== 1. pre-swap state =="
md5sum "$CS/allST/Application.app"

echo "== 2. backup current (patched) allST =="
mkdir -p "$CS/BACKUP_prehome_swap_$TS"
cp -p "$CS/allST/Application.app" "$CS/allST/Application.crc" "$CS/BACKUP_prehome_swap_$TS/"
ls -le "$CS/BACKUP_prehome_swap_$TS/"

echo "== 3. swap in ORIGINAL app =="
cp -p "$CS/BACKUP_ORIGINAL/Application.app" "$CS/allST/Application.app.tmp"
cp -p "$CS/BACKUP_ORIGINAL/Application.crc"  "$CS/allST/Application.crc.tmp"
mv -f "$CS/allST/Application.app.tmp" "$CS/allST/Application.app"
mv -f "$CS/allST/Application.crc.tmp" "$CS/allST/Application.crc"
sync

echo "== 4. verify =="
md5sum "$CS/allST/Application.app" "$CS/BACKUP_ORIGINAL/Application.app"
ls -le "$CS/allST/"

EXPECT=8416cf0eee070a640702c077eb904b4e
GOT=$(md5sum "$CS/allST/Application.app" | awk '{print $1}')
if [ "$GOT" != "$EXPECT" ]; then
  echo "MD5 MISMATCH - ABORT, no reboot. Restore manually from BACKUP_prehome_swap_$TS"
  exit 1
fi
echo "MD5 OK - rebooting in 3s ..."
sleep 3
reboot
