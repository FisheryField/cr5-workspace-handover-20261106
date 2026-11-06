#!/bin/sh
/mToolServer/tcpdump -i eth2 -s 0 -c 1500 -w /tmp/trial.pcap 2>&1 | tail -3
ls -la /tmp/trial.pcap
echo "=== 前 3 个包的帧长/类型 ==="
/mToolServer/tcpdump -r /tmp/trial.pcap -nn -e 2>/dev/null | head -5
