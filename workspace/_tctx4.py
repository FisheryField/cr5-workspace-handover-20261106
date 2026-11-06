import re
data = open(r"D:\software\dobot\DobotStudio Pro\resources\dobotlink\IndustrialRobotPlugin.dll","rb").read()
i = 0xaf6bc
win = data[max(0,i-1200):i+600]
for s in re.finditer(rb"[ -~]{5,}", win):
    print("  ", hex(max(0,i-1200)+s.start()), s.group().decode())
