
import csv, io, collections
p = r"D:\software\dobot\V1.3.4-stable\upgradeFiles\servoParamTemplate\CR_Param.csv"
raw = open(p,'rb').read()
txt = raw.decode('gbk', errors='replace')
rows = list(csv.reader(io.StringIO(txt)))
print("行数 =", len(rows))
print("表头 =", rows[0])
print()
# 找含 zero/home/offset/encoder 的行
keys = ('zero','Zero','home','Home','offset','Offset','encoder','Encoder','原点','零点','偏置','绝对','ABS','abs')
for r in rows[1:]:
    j = ','.join(r)
    if any(k in j for k in keys):
        print("  ", r[:8])
