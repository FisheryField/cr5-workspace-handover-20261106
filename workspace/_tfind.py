import re
data = open(r"D:\software\dobot\DobotStudio Pro\resources\dobotlink\IndustrialRobotPlugin.dll","rb").read()
for pat in [b"ClearError", b"ClearAlarms2", b"clearError"]:
    hits = [hex(m.start()) for m in re.finditer(re.escape(pat), data)]
    print(pat, hits[:10])
