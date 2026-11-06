
d = open(r"D:\mydata\workspace\data\Application.app",'rb').read()
pat = d[0x0e9f08:0x0e9f08+24]      # "Device.Application.IoConf"
print("文件 @0x0e9f08 的 24 字节:", pat.hex())
open(r"D:\mydata\workspace\data\app_pat.hex","w").write(pat.hex())
