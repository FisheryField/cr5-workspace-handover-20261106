#!/bin/sh
for IF in any eth2 eth0; do
  rm -f /tmp/t_$IF.pcap
  /mToolServer/tcpdump -i $IF -s 0 -w /tmp/t_$IF.pcap > /dev/null 2>&1 &
  TP=$!
  sleep 3
  kill $TP 2>/dev/null
  sleep 1
  echo "--- $IF ---"
  ls -la /tmp/t_$IF.pcap 2>/dev/null
  /mToolServer/tcpdump -r /tmp/t_$IF.pcap -nn -e -c 3 2>/dev/null | head -4
done
