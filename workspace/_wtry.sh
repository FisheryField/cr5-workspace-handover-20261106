echo "########## 对照组: 0x607C (已知可写) ##########"
/tmp/ecat_zero rv 8 0x607C 0
/tmp/ecat_zero wv 8 0x607C 0 12345
/tmp/ecat_zero rv 8 0x607C 0
/tmp/ecat_zero wv 8 0x607C 0 0
/tmp/ecat_zero rv 8 0x607C 0
echo
echo "########## 目标1: H01.17 编码器位置角 = 0x2001:18 ##########"
/tmp/ecat_zero rv 8 0x2001 18
echo "--- 试写 330 ---"
/tmp/ecat_zero wv 8 0x2001 18 330
echo "--- 回读 ---"
/tmp/ecat_zero rv 8 0x2001 18
echo
echo "########## 目标2: H0C.00 故障复位 = 0x200C:1 ##########"
/tmp/ecat_zero rv 8 0x200C 1
/tmp/ecat_zero wv 8 0x200C 1 0
/tmp/ecat_zero rv 8 0x200C 1
echo
echo "########## 目标3: H00.20 内部调试模式使能 = 0x2000:21 ##########"
/tmp/ecat_zero rv 8 0x2000 21
/tmp/ecat_zero wv 8 0x2000 21 0
