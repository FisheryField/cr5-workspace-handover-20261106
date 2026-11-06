import re
data = open(r'D:\software\dobot\DobotStudio Pro\resources\dobotlink\IndustrialRobotPlugin.dll', 'rb').read()
# find the offset of the standalone 'Exchange' string and the /protocol/exchange strings
for m in re.finditer(rb'[ -~]{4,}', data):
    s = m.group(0)
    if s == b'Exchange' or s == b'/protocol/exchange':
        print(hex(m.start()), repr(s))
        # print neighboring printable strings (context)
        ctx = data[max(0, m.start()-400):m.start()+400]
        parts = re.findall(rb'[ -~]{4,}', ctx)
        for p in parts:
            print('    ', repr(p)[:160])
        print('---')
