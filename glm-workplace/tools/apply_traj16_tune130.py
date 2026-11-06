"""Apply the fully prechecked two-retreat orientation edit with a backup."""
import json, hashlib, shutil, os, datetime
from pathlib import Path
base = Path(__file__).resolve().parents[1]
folder = base/'sim_scripts/rdk_station_dump/traj16_tune130_20261029_151605'
report = json.loads((folder/'result.json').read_text(encoding='utf-8'))
proposal, = [c for c in report['candidates'] if c['label']=='B_P18_P22']
assert proposal['result']=='PASS' and report['trajectory_unchanged']
path = Path(report['file'])
data = path.read_bytes()
assert hashlib.sha256(data).hexdigest()==report['input_sha256'], 'Trajectory changed since validation'
before = json.loads(data.decode('utf-8-sig'))
after = proposal['records']
assert len(before)==len(after)==23
changes = []
for i,(a,b) in enumerate(zip(before,after),1):
    if a != b:
        assert i in (18,22)
        assert a['values'][:3]==b['values'][:3]
        expected = dict(a, values=a['values'][:3]+b['values'][3:6])
        assert expected==b
        changes.append(dict(point=i,before=a['values'],after=b['values']))
assert [c['point'] for c in changes]==[18,22]
backup = path.with_name(path.stem+'_before_tcp130_tuning_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.json.bak')
shutil.copy2(path,backup)
temp = path.with_name(path.name+'.tune130.tmp')
temp.write_text(json.dumps(after,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert json.loads(temp.read_text(encoding='utf-8'))==after
os.replace(temp,path)
assert json.loads(path.read_text(encoding='utf-8'))==proposal['records']
receipt = dict(file=str(path),backup=str(backup),changes=changes,tested_tcp_mm=130,
               sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
               baseline_metrics=report['baseline_metrics'],optimized_metrics=proposal['metrics'],
               note='23 points; only retreat orientations P18/P22 changed; no hardware or canonical TCP changes')
(folder/'applied.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(receipt,ensure_ascii=False,indent=2))
