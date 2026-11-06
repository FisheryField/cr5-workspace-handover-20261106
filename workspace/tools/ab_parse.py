
import tarfile, struct, sys
tf = tarfile.open(sys.argv[1],'r:gz')
raw=None; ts=None; meta=''
for m in tf.getmembers():
    if m.name.endswith('ab_raw.bin'): raw=tf.extractfile(m).read()
    if m.name.endswith('ab_ts.txt'):  ts=tf.extractfile(m).read().decode().split()
    if m.name.endswith('ab_meta.txt'): meta=tf.extractfile(m).read().decode()
print(meta.strip())
N=len(raw)//96
print("records=%d  timestamps=%d" % (N, len(ts)))
t0=float(ts[0])
rows=[]
for i in range(N):
    rec=raw[i*96:(i+1)*96]
    v=[struct.unpack_from('<d',rec,o)[0] for o in (0,16,32,48,64,80)]
    rows.append((float(ts[i])-t0, v))
# 事件：任一轴变化 > 0.002
prev=None
print()
print("  t(s)     J1        J2        J3        J4        J5        J6      | 变化轴")
events=0
for t,v in rows:
    if prev is None:
        print("  %7.2f  %9.4f %9.4f %9.4f %9.4f %9.4f %9.4f  | (基线)" % (t,*v))
    else:
        ch=[j+1 for j in range(6) if abs(v[j]-prev[j])>0.002]
        if ch:
            events+=1
            if events<=80:
                print("  %7.2f  %9.4f %9.4f %9.4f %9.4f %9.4f %9.4f  | J%s" % (t,*v, ','.join(map(str,ch))))
    prev=v
print("... 共 %d 个变化事件" % events)
print()
print("=== 末尾 6 个样本 ===")
for t,v in rows[-6:]:
    print("  %7.2f  %9.4f %9.4f %9.4f %9.4f %9.4f %9.4f" % (t,*v))
print()
print("=== 每 5 秒抽样 ===")
for i in range(0,N,46):
    t,v=rows[i]
    print("  %7.2f  %9.4f %9.4f %9.4f %9.4f %9.4f %9.4f" % (t,*v))
