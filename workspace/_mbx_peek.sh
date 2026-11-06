for st in 0x3f0 0x3eb; do
  echo "########## 站 $st ##########"
  echo "--- SM 寄存器 ---"
  /tmp/ecat_mbx sregs eth0 $st
  echo "--- 读邮箱 0x1a30 (SM1) ---"
  /tmp/ecat_mbx peek eth0 $st 0x1a30 48
  echo "--- 写邮箱 0x1800 (SM0) ---"
  /tmp/ecat_mbx peek eth0 $st 0x1800 48
  echo
done
