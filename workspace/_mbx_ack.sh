ACK="00000000000000000000000000000000000000000000"
for st in 0x3f0 0x3eb; do
  echo "########## 站 $st ##########"
  echo "--- 1) 从 0x1a20 写 22 个 0 (确认/清空 SM1) ---"
  /tmp/ecat_mbx poke eth0 $st 0x1a20 $ACK
  echo "--- 2) SM 状态 ---"
  /tmp/ecat_mbx sregs eth0 $st | head -3
  echo "--- 3) 写 SDO 请求 (读 0x6064) ---"
  /tmp/ecat_mbx poke eth0 $st 0x1800 0a000000002300204064600000000000
  sleep 0.05
  echo "--- 4) 看读窗口 0x1a20 ---"
  /tmp/ecat_mbx peek eth0 $st 0x1a20 48
  echo
done
