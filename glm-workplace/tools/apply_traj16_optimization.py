"""Back up trajectory16, then atomically apply the fully prechecked point reduction."""
import datetime, hashlib, json, os, shutil
from pathlib import Path
base = Path(__file__).resolve().parents[1]
folder = base/'sim_scripts'/'rdk_station_dump'/'traj16_precheck_20261027_145923'
proposal = json.loads((folder/'optimization_remove_P12_P13.json').read_text(encoding='utf-8'))
baseline = json.loads((folder/'result.json').read_text(encoding='utf-8'))
path = Path(baseline['file'])
original = path.read_bytes()
assert proposal['result'] == 'PASS'
assert hashlib.sha256(original).hexdigest() == proposal['input_sha256'], 'Source changed; refuse overwrite'
old = json.loads(original.decode('utf-8-sig'))
new = proposal['records']
assert new == [rec for idx,rec in enumerate(old,1) if idx not in (12,13)]
stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
backup = path.with_name(path.stem+'_before_flowopt_'+stamp+'.json.bak')
shutil.copy2(path, backup)
temporary = path.with_name(path.name+'.flowopt.tmp')
temporary.write_text(json.dumps(new, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
assert json.loads(temporary.read_text(encoding='utf-8')) == new
os.replace(temporary,path)
receipt = dict(backup=str(backup), file=str(path), removed_original_points=[12,13],
               old_points=len(old),new_points=len(new),
               original_sha256=hashlib.sha256(original).hexdigest(),
               new_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
               mapping=[dict(new_point=i+1, original_point=i+1 if i<11 else i+3) for i in range(len(new))])
(folder/'applied_optimization.json').write_text(json.dumps(receipt, ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(receipt,ensure_ascii=False,indent=2))
