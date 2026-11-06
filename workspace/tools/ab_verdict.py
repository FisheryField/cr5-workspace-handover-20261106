
import tarfile, struct, sys, datetime
tf = tarfile.open(sys.argv[1],'r:gz')
for m in tf.getmembers():
    if m.name.endswith('ab_raw.bin'): raw=tf.extractfile(m).read()
    if m.name.endswith('ab_ts.txt'):  ts=tf.extractfile(m).read().decode().split()
N=len(raw)//96
rows=[]
for i in range(N):
    rec=raw[i*96:(i+1)*96]
    v=[struct.unpack_from('<d',rec,o)[0] for o in (0,16,32,48,64,80)]
    rows.append((float(ts[i])-float(ts[0]), v))
# 锚点: t=87.93 对应 15:55:09.27 (标定 POST)
anchor_t = 87.93
anchor_wall = datetime.datetime(2026,9,23,15,55,9,270000)
def wall(t): return (anchor_wall + datetime.timedelta(seconds=(t-anchor_t))).strftime('%H:%M:%S.%f')[:-3]
def at(t):
    best=min(rows, key=lambda r: abs(r[0]-t)); return best
print(" 墙钟时间      t(s)     J1       J2       J3       J4       J5       J6")
for label,t in [("基线(未使能)",0.0),("①上使能前",81.2),("①上使能后",82.0),
                ("②标定前",87.8),("②标定后",88.7),("③下使能后",95.0),
                ("④上使能前",101.8),("④上使能后",102.2),("④稳定后(+60s)",165.0)]:
    tt,v=at(t)
    print("  %s  %6.2f  %8.4f %8.4f %8.4f %8.4f %8.4f %8.4f   ← %s" % (wall(tt),tt,*v,label))
print()
_,vb=at(81.2); _,va=at(82.0)
print("① 上使能瞬间 J6: %.4f → %.4f   Δ=%+.4f°   (J1~J5 未变)" % (vb[5],va[5],va[5]-vb[5]))
_,vb=at(101.8); _,va=at(102.2); _,vc=at(165.0)
print("② 标定后 J6 = %.4f" % at(88.7)[1][5])
print("④ 重新上使能 J6: %.4f → %.4f   Δ=%+.4f°" % (vb[5],va[5],va[5]-vb[5]))
print("④ 稳定后 J6 = %.4f" % vc[5])
print()
print("④ 之后 J1~J5 的稳定残差(物理摇晃): %s" % ['%+.4f'%x for x in vc[:5]])
print("   J1~J5 残差幅度 ~%.3f°" % max(abs(x) for x in vc[:5]))
print("   J6 = %.4f°  ⇒ 比 J1~J5 大 %.1f 倍" % (vc[5], abs(vc[5])/max(abs(x) for x in vc[:5])))
print()
print("④ 之后 J1~J5 相对 J6 的偏移: J6 - mean(J1..J5) = %+.4f°" % (vc[5]-sum(vc[:5])/5))
