echo "########## mode 0: 单帧 512B 写 ##########"
/tmp/ecat_mbx diag eth0 0x3f0 0x6064 0 0
echo
echo "########## mode 1: 先 body 后 header ##########"
/tmp/ecat_mbx diag eth0 0x3f0 0x6064 0 1
