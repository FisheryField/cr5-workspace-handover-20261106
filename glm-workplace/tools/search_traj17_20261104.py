"""Read the live scene and test Y-3 variants in a separate simulation instance."""
from pathlib import Path
import json, hashlib, datetime, io, sys, struct, copy, traceback
import numpy as np
from robodk.robolink import *
from robodk.robomath import *
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',line_buffering=True)
root=Path(__file__).resolve().parents[1]
out=root/'sim_scripts/rdk_station_dump'/('traj17_search_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
out.mkdir(parents=True)
path=Path(r'D:\mydata\working things\dobot_arm\RoboDK files 2\连续轨迹16.json')
data=path.read_bytes(); original=json.loads(data.decode('utf-8-sig'))
main=Robolink(port=20500); body=main.Item('Dobot CR5',ITEM_TYPE_ROBOT)
before=dict(mode=main.RunMode(),joints=body.Joints().list(),tool=body.PoseTool().rows,
    frame=body.PoseFrame().rows,base=body.PoseAbs().rows)
source=out/'station_p2p.py'
macros=[it for it in main.ItemList(ITEM_TYPE_PROGRAM_PYTHON)
    if it.Name() in ('TCP真实运动_P2P版','TCP真实运动_P2P版_16稳定版')]
assert len(macros)==1,[(it.Name(),it.Type()) for it in macros]
macros[0].Save(str(source))
code=source.read_text(encoding='utf-8').split('root = tk.Tk()')[0]
assert 'v15.21-20261103' in code
snapshot=[]
for name in ['门把手_bs1','安装台_650x650x80mm','地面_禁止穿越','磨砂圆柱_R150_H50','挡板_半封闭3面']:
    obj=main.Item(name,ITEM_TYPE_OBJECT)
    assert obj.Valid(),name
    pts,_=obj.GetPoints(FEATURE_OBJECT_MESH)
    file=out/(name+'.stl')
    buf=bytearray(b'offline read-only mesh snapshot'.ljust(80,b' '))+struct.pack('<I',len(pts)//3)
    for i in range(0,len(pts),3):
        buf+=struct.pack('<12fH',0,0,0,*[float(x) for row in pts[i:i+3] for x in row[:3]],0)
    file.write_bytes(buf)
    snapshot.append(dict(name=name,file=str(file),pose=obj.Pose().rows,
        absolute=obj.PoseAbs().rows,geometry=obj.GeometryPose().rows))
sim=Robolink(port=20501)
assert sim.PORT==20501
sim.setRunMode(RUNMODE_SIMULATE)
assert not sim.ItemList(ITEM_TYPE_ROBOT),'Expected an empty isolated instance'
model=sim.AddFile(str(root/'sim_scripts/rdk_station_dump/body_alignment_20261103/final_aligned_body.robot'))
model.setName('Dobot CR5')
parent=model.Parent()
parent.setPose(Mat(before['base'])*invH(model.PoseAbs())*parent.PoseAbs())
for item in snapshot:
    obj=sim.AddFile(item['file']); obj.setName(item['name']); obj.setGeometryPose(Mat(item['geometry']))
    if item['name']=='门把手_bs1':
        obj.setParent(model); obj.setPose(Mat(item['pose']))
    else:
        obj.setPose(Mat(item['absolute']))
tool=model.AddTool(transl(0,0,130),'CR5_TCP_130mm')
model.setPoseTool(tool);model.setPoseFrame(Mat(before['frame']))
for name in ['磨砂圆柱_R150_H50','挡板_半封闭3面']:
    a=invH(body.PoseAbs())*main.Item(name).PoseAbs()
    b=invH(model.PoseAbs())*sim.Item(name).PoseAbs()
    assert np.max(np.abs(np.array(a.rows)-np.array(b.rows)))<1e-4

def forbidden(*a,**k): raise AssertionError('Hardware access forbidden in this test')
reports=[]
try:
    for dy,dz in [(y,z) for y in [5,10,15,20,30,40,60,80] for z in [0,-10,-20,-40]]:
        case='dy%d_dz%d'%(dy,dz)
        points=list(range(2,23))
        candidate=copy.deepcopy(original)
        for n in points:
            candidate[n-1]['values'][1]+=dy
            candidate[n-1]['values'][2]+=dz
        shift=Mat(before['base'])*transl(0,dy,dz)*invH(Mat(before['base']))
        for item in snapshot:
            if item['name'] in ['磨砂圆柱_R150_H50','挡板_半封闭3面']:
                sim.Item(item['name']).setPose(shift*Mat(item['absolute']))
        file=out/(case+'.json')
        file.write_text(json.dumps(candidate,ensure_ascii=False,indent=2),encoding='utf-8')
        ns={}
        exec(compile(code.replace('RDK = Robolink()','RDK = Robolink(port=20501)'),str(source),'exec'),ns)
        ns.update(ensure_connected=forbidden,_controller_feedback=forbidden,
            _live_joints=forbidden,_single_move_settle=forbidden)
        records=ns['_retreat_orientation_records'](ns['_validated_records'](candidate))
        production_match=None
        test_hash=ns['_records_fingerprint'](records)
        logs=[]
        def log(message):
            logs.append(str(message));print(case,str(message),flush=True)
        ns.update(log=log,_file_log=log)
        model.setPoseTool(tool);model.setPoseFrame(Mat(before['frame']));model.setJoints([0]*6)
        result=dict(dy=dy,dz=dz,case=case,changed_points=points,candidate_file=str(file),
            production_profile_matches=production_match,test_profile_hash=test_hash,
            original_trajectory_sha256=hashlib.sha256(data).hexdigest(),
            script_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),start_joints=[0]*6,
            tcp=Pose_2_Fanuc(model.PoseTool()),hardware_access=False)
        try:
            plan=ns['_plan_continuous_trajectory'](records,500.0,log)
            ns['_assert_continuous_dispatch'](records,[0]*6,plan,True)
            result.update(result='PASS',plan=plan,linear_certified=[i for i,s in enumerate(plan,1) if s.get('direct_movl_certified')])
        except Exception as exc:
            result.update(result='FAIL',error=type(exc).__name__+': '+str(exc))
            print('CASE_FAIL',case,result['error'],flush=True)
        result['logs']=logs
        reports.append(result)
        (out/'result.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf-8')
        print('CASE_RESULT',case,result['result'],flush=True)
        if result['result']=='PASS':
            target=path.with_name('连续轨迹17.json')
            assert not target.exists(), 'Trajectory17 already exists'
            target.write_text(json.dumps(candidate,ensure_ascii=False,indent=2),encoding='utf-8')
            placement=dict(translation_robot_base_mm=[0,dy,dz],objects=[dict(name=item['name'],original_absolute=item['absolute'],target_absolute=(shift*Mat(item['absolute'])).rows) for item in snapshot if item['name'] in ['磨砂圆柱_R150_H50','挡板_半封闭3面']],trajectory=str(target))
            (out/'placement.json').write_text(json.dumps(placement,ensure_ascii=False,indent=2),encoding='utf-8')
            break
finally:
    assert path.read_bytes()==data,'Original trajectory changed externally'
    after=dict(mode=main.RunMode(),joints=body.Joints().list(),tool=body.PoseTool().rows,
        frame=body.PoseFrame().rows,base=body.PoseAbs().rows)
    (out/'scene_snapshot.json').write_text(json.dumps(dict(before=before,after=after,items=snapshot),ensure_ascii=False,indent=2),encoding='utf-8')
    print('REPORT',out/'result.json',flush=True)
    sim.CloseRoboDK()
