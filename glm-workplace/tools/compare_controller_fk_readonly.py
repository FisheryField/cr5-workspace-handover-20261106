"""Only calculation/status commands; no state changes or motion commands."""
import socket,json,re,datetime,sys,io
from pathlib import Path
from robodk.robolink import Robolink,ITEM_TYPE_ROBOT
from robodk.robomath import Pose_2_Fanuc
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace',line_buffering=True)
report_path=Path('sim_scripts/rdk_station_dump/traj16_tcp130_20261103_154825/result.json')
baseline=json.loads(report_path.read_text(encoding='utf-8'))
out=Path('sim_scripts/rdk_station_dump')/('controller_fk_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'));out.mkdir()
r=Robolink(port=20500);robot=r.Item('',ITEM_TYPE_ROBOT)
report={'queries':[],'samples':[]}
def query(cmd):
    assert cmd.split('(')[0] in ('RobotMode','PositiveSolution','PositiveKin','InverseSolution','InverseKin')
    with socket.create_connection(('192.168.5.1',29999),timeout=5) as s:
        s.settimeout(5);s.sendall(cmd.encode());b=b''
        while b';' not in b:
            c=s.recv(4096)
            if not c:break
            b+=c
    result=b.decode('utf-8',errors='replace')
    report['queries'].append(dict(command=cmd,response=result))
    print(cmd,result,flush=True)
    (out/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    m=re.match(r'\s*0\s*,\s*\{([^{}]*)\}',result)
    if not m:return None
    try:return [float(v) for v in m.group(1).split(',')]
    except ValueError:return None
mode=query('RobotMode()')
assert mode, 'Status query returned no data; cannot determine controller state. Existing dashboard client may occupy port.'
assert mode[0]!=7,'Controller is running; stop this diagnostic'
syntax=None
for label,q in [('zero',[0]*6)]+[(f'P{i}',baseline['plan'][i-1]['joints']) for i in (8,9,10,11)]:
    args=','.join('%.9f'%v for v in q)
    fk=None
    for name in ([syntax] if syntax else ['PositiveSolution','PositiveKin']):
        cmd=(f'{name}({args},0,0)' if name=='PositiveSolution' else f'{name}({args},user=0,tool=0)')
        fk=query(cmd)
        if fk and len(fk)==6:syntax=name;break
    entry=dict(label=label,joints=q,robodk_flange=Pose_2_Fanuc(robot.SolveFK(q)),controller_flange=fk)
    report['samples'].append(entry)
    if fk is None:break
report['note']='Calculation/status requests only; no Tool/User/Enable/motion calls'
(out/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('REPORT',out/'result.json',flush=True)
