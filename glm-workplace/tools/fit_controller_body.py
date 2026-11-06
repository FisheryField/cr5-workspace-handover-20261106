"""Read-only controller FK sampling and local MDH fit; no robot edits/motion."""
import socket,json,itertools,math,sys,io
from pathlib import Path
import numpy as np
from robodk.robolink import *
from robodk.robomath import Pose_2_Fanuc,Fanuc_2_Pose
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace',line_buffering=True)
out=Path('sim_scripts/rdk_station_dump/body_alignment_20261103');out.mkdir(exist_ok=True)
r=Robolink(port=20500);b=r.Item('Dobot CR5',ITEM_TYPE_ROBOT)
report=json.loads(Path('sim_scripts/rdk_station_dump/traj16_tcp130_20261103_154825/result.json').read_text(encoding='utf-8'))
qs=[[0.0]*6]+[s['joints'] for s in report['plan']]
rng=np.random.RandomState(16)
qs += [list(rng.uniform([-100,-40,-90,-80,-100,-150],[100,40,90,80,100,150])) for _ in range(22)]
connection=socket.create_connection(('192.168.5.1',29999),5)
connection.settimeout(5)
def query(cmd):
    assert cmd.startswith(('PositiveSolution(','RobotMode('))
    connection.sendall(cmd.encode());reply=b''
    while b';' not in reply:
        part=connection.recv(4096)
        if not part:break
        reply+=part
    txt=reply.decode();assert txt.startswith('0,'),txt
    return [float(v) for v in txt.split('{')[1].split('}')[0].split(',')]
assert query('RobotMode()')==[5]
samples=[]
for i,q in enumerate(qs):
    pose=query('PositiveSolution('+','.join('%.9f'%(0 if abs(v)<1e-8 else v) for v in q)+',0,0)')
    samples.append(dict(q=q,controller_pose=pose,robodk_pose=Pose_2_Fanuc(b.SolveFK(q))))
(out/'fk_samples.json').write_text(json.dumps(samples,indent=2),encoding='utf-8')
connection.close()
print('SAMPLED',len(samples),flush=True)
# Each row: alpha(deg), a(mm), theta-offset(deg), d(mm), modified DH.
nom=np.array([[0,0,0,147],[90,0,90,0],[0,427,0,0],[0,357,-90,141],[-90,0,0,116],[90,0,180,100.5]],float)
def fk(par,q,sign):
    T=np.eye(4)
    for row,v,s in zip(par,q,sign):
        al,a,th,d=row;al=math.radians(al);th=math.radians(th+s*v)
        ca,sa,ct,st=math.cos(al),math.sin(al),math.cos(th),math.sin(th)
        A=np.array([[ct,-st,0,a],[st*ca,ct*ca,-sa,-d*sa],[st*sa,ct*sa,ca,d*ca],[0,0,0,1]])
        T=T@A
    return T
def mat(vals):return np.array(Fanuc_2_Pose(vals).rows)
sign=min(itertools.product((-1,1),repeat=6),key=lambda ss:sum(np.linalg.norm(fk(nom,s['q'],ss)-mat(s['robodk_pose'])) for s in samples[:5]))
nomerr=max(np.linalg.norm(fk(nom,s['q'],sign)-mat(s['robodk_pose'])) for s in samples)
print('NOMINAL_SIGNS',sign,'ERROR',nomerr,flush=True);assert nomerr<1e-5
targets=[mat(s['controller_pose']) for s in samples]
def residual(x,indices):
    par=nom+x.reshape(6,4)
    parts=[]
    for i in indices:
        A=fk(par,samples[i]['q'],sign);B=targets[i]
        parts.extend(A[:3,3]-B[:3,3]);parts.extend(((A[:3,:3]-B[:3,:3])*100).ravel())
    return np.array(parts)
# Hold out every fourth pose for independent validation.
train=[i for i in range(len(samples)) if i%4];valid=[i for i in range(len(samples)) if not i%4]
x=np.zeros(24)
for iteration in range(50):
    y=residual(x,train);J=np.column_stack([(residual(x+np.eye(24)[j]*1e-4,train)-y)/1e-4 for j in range(24)])
    dx=np.linalg.lstsq(np.vstack((J,np.eye(24)*1e-5)),np.r_[-y,np.zeros(24)],rcond=1e-9)[0]
    accepted=False
    for f in (1,.5,.25,.1,.01):
        xn=x+f*dx
        if np.max(np.abs(xn))>15:continue
        if np.linalg.norm(residual(xn,train))<np.linalg.norm(y):x=xn;accepted=True;break
    print('FIT',iteration,float(np.linalg.norm(y)),flush=True)
    if np.linalg.norm(y)<1e-4 or not accepted:break
par=nom+x.reshape(6,4)
errors=[]
for i,s in enumerate(samples):
    A=fk(par,s['q'],sign);B=targets[i];R=A[:3,:3].T@B[:3,:3]
    errors.append(dict(index=i,held_out=i in valid,mm=float(np.linalg.norm(A[:3,3]-B[:3,3])),deg=math.degrees(math.acos(np.clip((np.trace(R)-1)/2,-1,1)))))
result=dict(mdh=par.tolist(),nominal_mdh=nom.tolist(),joint_signs=sign,errors=errors,max_mm=max(e['mm'] for e in errors),max_deg=max(e['deg'] for e in errors))
(out/'fit.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('RESULT',result['max_mm'],result['max_deg'],par.tolist(),flush=True)
