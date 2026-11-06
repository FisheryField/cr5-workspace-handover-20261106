
import csv, io
p = r"D:\software\dobot\V1.3.4-stable\upgradeFiles\servoParamTemplate\CR_Param.csv"
rows = list(csv.reader(io.StringIO(open(p,'rb').read().decode('gbk', errors='replace'))))
hdr = rows[1]
data = [r for r in rows[2:] if len(r)>3 and r[3]]
ci=hdr.index('ParaIndex'); cnm=hdr.index('ParaName'); cm=hdr.index('ParaMapIndex')
cro=hdr.index('ReadOnly'); cu=hdr.index('Unit'); cmin=hdr.index('MIN'); cmax=hdr.index('MAX')
cval=hdr.index('ParaValue')
def C(s): return s.encode('utf-8','replace').decode('utf-8')
for g in ['H0A','H0B','H0C','H05','H06','H07','H09']:
    print("=== %s ===" % g)
    for r in data:
        if r[ci].startswith(g+'.'):
            print("   %-8s map=%-4s ro=%-5s val=%-8s %-30s [%s,%s]" % (r[ci],r[cm],r[cro],r[cval][:8],r[cnm][:30],r[cmin][:7],r[cmax][:7]))
    print()
