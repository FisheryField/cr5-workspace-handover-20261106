"""Determine inverse-query angle semantics using known FK poses, no motion."""
from pathlib import Path
import math
src=Path(__file__).with_name('compare_controller_fk_readonly.py').read_text(encoding='utf-8')
exec(compile(src[:src.index("mode=query('RobotMode()')")],'<readonly-query-setup>','exec'))
mode=query('RobotMode()');assert mode and mode[0]==5
fk_report=json.loads(Path('sim_scripts/rdk_station_dump/controller_fk_20261103_160250/result.json').read_text(encoding='utf-8'))
report['unit_tests']=[]
for sample in (fk_report['samples'][0],fk_report['samples'][-1]):
    pose=sample['controller_flange']
    for name,vals in [('degrees',pose),('radians',pose[:3]+[math.radians(v) for v in pose[3:]])]:
        for api in (['InverseSolution','InverseKin'] if name=='degrees' else ['InverseSolution']):
            args=','.join('%.9f'%v for v in vals)
            suffix=',0,0' if api=='InverseSolution' else ',user=0,tool=0'
            result=query(api+'('+args+suffix+')')
            report['unit_tests'].append(dict(label=sample['label'],units=name,api=api,values=vals,result=result))
report['note']='Read-only status and inverse calculations; no motion commands'
(out/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('REPORT',out/'result.json')
