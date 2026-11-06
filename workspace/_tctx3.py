import re
data = open(r"D:\software\dobot\DobotStudio Pro\resources\dobotlink\IndustrialRobotPlugin.dll","rb").read()
i = data.find(b"\x00Exchange\x00")
print("Exchange @", hex(i))
win = data[max(0,i-800):i+800]
for s in re.finditer(rb"[ -~]{5,}", win):
    print("  ", hex(max(0,i-800)+s.start()), s.group().decode())
