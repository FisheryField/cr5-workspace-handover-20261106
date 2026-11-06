chmod +x /tmp/ecat_mbx
/tmp/ecat_mbx home eth0 0x3f0 2>&1 | grep -avE "^      \[[0-3][0-9]\] sw=0x8250"
