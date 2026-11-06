data = open(r"D:\software\dobot\DobotStudio Pro\resources\dobotlink\IndustrialRobotPlugin.dll","rb").read()
i = data.find(b"/protocol/exchange")
print("offset", hex(i))
# dump printable strings in surrounding window
import re
win = data[max(0,i-3000):i+3000]
for m in re.finditer(rb"[ -~]{5,}", win):
    print(hex(max(0,i-3000)+m.start()), m.group().decode())
