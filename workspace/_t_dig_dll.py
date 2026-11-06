import re
data = open(r'D:\software\dobot\DobotStudio Pro\resources\dobotlink\IndustrialRobotPlugin.dll', 'rb').read()
for pat in [b'httpClient', b'src', b'Exchange', b'exchange']:
    hits = [m for m in re.finditer(rb'[ -~]{6,}', data) if pat in m.group(0)]
    print('PAT', pat, 'count', len(hits))
    for m in hits[:8]:
        print('   ', repr(m.group(0))[:280])
    print()
