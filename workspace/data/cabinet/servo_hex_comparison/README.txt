用途：与桌面的3.1.5.hex做应用区对比，未验证可直接烧录。
源文件：D:\software\DobotStudio\V1.3.4-stable\V1.3.4-stable\upgradeFiles\3.5.6\3.5.6.1\files\CR5_Servo_ST_FOE_V3.2.D.8.bin
处理：验证并去除32字节FOE升级头；保留全部程序数据；按推定地址0x08010000编码为Intel HEX。
地址范围：0x8010000—0x8062897（含末地址）。
没有补入Bootloader或补齐到1MiB。未添加启动地址记录。
每条记录校验通过，解码回读与原BIN程序部分逐字节一致。
比较时应按解码后的地址比较，不要仅按文本行或文件大小比较。
