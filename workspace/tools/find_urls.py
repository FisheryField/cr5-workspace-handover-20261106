
import re
p = r'D:\software\dobot\V1.3.4-stable\RobotMaintenanceTools.exe'
d=open(p,'rb').read()
pat = re.compile(rb'/[A-Za-z][A-Za-z0-9_/]{3,60}')
seen={}
for m in pat.finditer(d):
    s=m.group(0).decode('latin-1')
    if any(k in s for k in ('/properties','/interface','/servo','/settings','/param','/calibrate','/protocol','/update','/fault','/connection','/device','/driver')):
        seen[s]=seen.get(s,0)+1
for s,c in sorted(seen.items(), key=lambda x:-x[1]):
    print("%5d  %s" % (c,s))
