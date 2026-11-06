
import re
d = open(r"D:\mydata\workspace\data\Application.app",'rb').read()
def dump(center, before=500, after=900, title=""):
    print("="*90)
    print("### %s  @0x%06x" % (title, center))
    seg = d[max(0,center-before): center+after]
    base = max(0,center-before)
    for m in re.finditer(rb'[\x20-\x7e]{3,120}', seg):
        print("   0x%06x  %s" % (base+m.start(), m.group().decode('latin-1')[:118]))
i = d.find(b'/tmp/ServoParamsWrite')
dump(i, 600, 1200, "/tmp/ServoParamsWrite 邻域")
j = d.find(b'ServoParams\r')
if j<0: j = d.find(b'ServoParams')
dump(j, 400, 500, "ServoParams 邻域")
