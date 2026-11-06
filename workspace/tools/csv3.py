
import csv, io
p = r"D:\software\dobot\V1.3.4-stable\upgradeFiles\servoParamTemplate\CR_Param.csv"
txt = open(p,'rb').read().decode('gbk', errors='replace')
rows = list(csv.reader(io.StringIO(txt)))
hdr = rows[1]
data = [r for r in rows[2:] if len(r)>3 and r[3]]
ci=hdr.index('ParaIndex'); cnm=hdr.index('ParaName'); cm=hdr.index('ParaMapIndex')
cro=hdr.index('ReadOnly'); cu=hdr.index('Unit'); cmin=hdr.index('MIN'); cmax=hdr.index('MAX')
for gname in ['H00','H01','H02','H0D','H0E','H05','H0C']:
    print("=== %s ===" % gname)
    for r in data:
        if r[ci].startswith(gname+'.'):
            print("   %-8s map=%-5s ro=%-5s %-28s %-8s [%s,%s]" % (
                r[ci], r[cm], r[cro], r[cnm][:28], r[cu][:8], r[cmin][:8], r[cmax][:8]))
    print()
