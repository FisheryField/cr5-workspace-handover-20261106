"""InverseSolution calculations only, comparing model and controller FK targets."""
from pathlib import Path
src=Path(__file__).with_name('compare_controller_fk_readonly.py').read_text(encoding='utf-8')
exec(compile(src[:src.index("mode=query('RobotMode()')")],'<readonly-query-setup>','exec'))
fk_report=json.loads(Path('sim_scripts/rdk_station_dump/controller_fk_20261103_160250/result.json').read_text(encoding='utf-8'))
mode=query('RobotMode()');assert mode and mode[0]==5
report['comparisons']=[]
for sample in fk_report['samples']:
    if sample['label']=='zero':continue
    results={}
    for kind in ('robodk_flange','controller_flange'):
        vals=sample[kind]
        results[kind]=query('InverseSolution('+','.join('%.9f'%v for v in vals)+',0,0)')
    report['comparisons'].append(dict(label=sample['label'],results=results))
samples={s['label']:s for s in fk_report['samples']}
report['controller_line_samples']=[]
for start,end in [('P8','P9'),('P10','P11')]:
    a=samples[start]['controller_flange'];b=samples[end]['controller_flange']
    for frac in (.25,.5,.75):
        # Unwrap Euler coordinates across +/-180 for these near-constant orientations.
        vals=[a[i]+(b[i]-a[i])*frac for i in range(3)]
        vals += [a[i]+((b[i]-a[i]+180)%360-180)*frac for i in range(3,6)]
        q=query('InverseSolution('+','.join('%.9f'%v for v in vals)+',0,0)')
        report['controller_line_samples'].append(dict(segment=start+'-'+end,fraction=frac,pose=vals,joints=q))
failed=[119.991436,-683.978442,590.035603,-179.997212,.001108,-180]
report['exact_failed_P11_ik']=query('InverseSolution('+','.join(str(v) for v in failed)+',0,0)')
(out/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('REPORT',out/'result.json')
