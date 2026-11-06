"""Exact triangle-surface distances, with AABB pruning; no RoboDK writes or hardware access."""
from pathlib import Path
import numpy as np,json,math,time
from robodk.robomath import Fanuc_2_Pose
p=Path('sim_scripts/rdk_station_dump/traj16_yz_20261103');g=json.loads((p/'clearance_geometry.json').read_text(encoding='utf-8'))
mat=lambda name:np.array(g[name],float)
H=np.c_[np.array(g['handle_points'])[:,:3],np.ones(len(g['handle_points']))]
M=np.linalg.inv(mat('cylinder_pose')@mat('cylinder_geometry'))@mat('robot_base')
HG=mat('handle_pose')@mat('handle_geometry')
C=np.array(g['cylinder_points'])[:,:3].reshape(-1,3,3);cv=np.unique(C.reshape(-1,3),axis=0);clo=C.min(1);chi=C.max(1)
# FK avoids changing the on-screen robot.
dh=np.array(json.loads(Path('sim_scripts/rdk_station_dump/body_alignment_20261103/exact_mdh.json').read_text(encoding='utf-8')))
def fk(q):
 T=np.eye(4)
 for (al,a,th,d),v in zip(dh,q):
  al,th=np.radians([al,th+v]);ca,sa,ct,st=np.cos(al),np.sin(al),np.cos(th),np.sin(th)
  T=T@np.array([[ct,-st,0,a],[st*ca,ct*ca,-sa,-d*sa],[st*sa,ct*sa,ca,d*ca],[0,0,0,1]])
 return T
D=lambda a,b:np.einsum('ij,ij->i',a,b)
def pointseg(x,a,b):
 u=b-a;t=np.clip(D(x-a,u)/np.maximum(D(u,u),1e-25),0,1);return D(x-a-t[:,None]*u,x-a-t[:,None]*u)
def pointtri(x,t):
 a,b,c=t[:,0],t[:,1],t[:,2];u=b-a;v=c-a;w=x-a;n=np.cross(u,v);nn=D(n,n);height=D(w,n)
 aa,bb,cc,dd,ee=D(u,u),D(u,v),D(v,v),D(w,u),D(w,v);den=aa*cc-bb*bb
 s=(cc*dd-bb*ee)/np.maximum(den,1e-25);z=(aa*ee-bb*dd)/np.maximum(den,1e-25)
 inside=(s>=0)&(z>=0)&(s+z<=1)&(nn>1e-20)
 edge=np.minimum.reduce([pointseg(x,a,b),pointseg(x,b,c),pointseg(x,c,a)])
 return np.where(inside,height*height/np.maximum(nn,1e-25),edge)
def segtri(x,y,t):
 u=t[:,1]-t[:,0];v=t[:,2]-t[:,0];direction=y-x;h=np.cross(direction,v);det=D(u,h);inv=np.divide(1.,det,out=np.zeros_like(det),where=np.abs(det)>1e-15);s=x-t[:,0];a=inv*D(s,h);q=np.cross(s,u);b=inv*D(direction,q);tt=inv*D(v,q)
 return (np.abs(det)>1e-15)&(a>=0)&(b>=0)&(a+b<=1)&(tt>=0)&(tt<=1)
def clearance(q):
 T=((M@fk(q)@HG)@H.T).T[:,:3].reshape(-1,3,3);tv=np.unique(T.reshape(-1,3),axis=0)
 upper=np.min(np.sum((tv[:,None,:]-cv[None,:,:])**2,axis=2))
 lo=T.min(1);hi=T.max(1);delta=np.maximum(np.maximum(lo[:,None,:]-chi[None,:,:],clo[None,:,:]-hi[:,None,:]),0)
 ix,jx=np.where(np.sum(delta*delta,axis=2)<=upper+1e-8);A,B=T[ix],C[jx];vals=np.full(len(ix),np.inf)
 for k in range(3):vals=np.minimum(vals,pointtri(A[:,k],B));vals=np.minimum(vals,pointtri(B[:,k],A))
 for i in range(3):
  a,b=A[:,i],A[:,(i+1)%3];u=b-a
  if np.any(segtri(a,b,B)) or np.any(segtri(B[:,i],B[:,(i+1)%3],A)):return 0.
  for j in range(3):
   c,d=B[:,j],B[:,(j+1)%3];v=d-c;w=a-c;aa,bb,cc,dd,ee=D(u,u),D(u,v),D(v,v),D(u,w),D(v,w);den=aa*cc-bb*bb
   s=np.divide(bb*ee-cc*dd,den,out=np.zeros_like(den),where=abs(den)>1e-20);t=np.divide(aa*ee-bb*dd,den,out=np.zeros_like(den),where=abs(den)>1e-20)
   z=w+s[:,None]*u-t[:,None]*v;valid=(abs(den)>1e-20)&(s>=0)&(s<=1)&(t>=0)&(t<=1);vals=np.minimum(vals,np.where(valid,D(z,z),np.inf))
 return float(np.sqrt(np.min(vals)))
if __name__=='__main__':
 report=json.loads(Path('sim_scripts/rdk_station_dump/traj16_yz_numeric_20261103_165218/result.json').read_text(encoding='utf-8'));data=json.loads(Path(report['file']).read_text(encoding='utf-8'));out=[];start=time.monotonic()
 for i,(s,d) in enumerate(zip(report['plan'],data),1):
  dist=clearance(s['joints']);rec=dict(point=i,rxyz=d['values'][3:],xyz=d['values'][:3],clearance_mm=dist);out.append(rec);print(json.dumps(rec),flush=True)
 (p/'clearance_endpoints.json').write_text(json.dumps(dict(cylinder_mesh_radius_mm=float(np.max(np.linalg.norm(cv[:,:2],axis=1))),endpoint_results=out,seconds=time.monotonic()-start),indent=2),encoding='utf-8')
