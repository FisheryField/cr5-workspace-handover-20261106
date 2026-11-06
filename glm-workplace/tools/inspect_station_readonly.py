"""Read the open RoboDK station; export Python source without executing it."""
import sys, io, json, hashlib, datetime
from pathlib import Path
from robodk.robolink import Robolink, ITEM_TYPE_PROGRAM_PYTHON
from robodk.robomath import Pose_2_Fanuc
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
rdk = Robolink(port=20500)
out = Path(__file__).resolve().parent.parent / 'sim_scripts' / 'rdk_station_dump' / ('inspection_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
out.mkdir(parents=True)
rows = []
for idx, item in enumerate(rdk.ItemList()):
    row = {'name': item.Name(), 'type': item.Type()}
    for key, fn in [('parent', lambda: item.Parent().Name()), ('visible', item.Visible)]:
        try: row[key] = fn()
        except Exception as e: row[key] = str(e)
    if row['type'] in (2, 3, 4, 5, 6):
        for key, fn in [('pose_local', item.Pose), ('pose_world', item.PoseAbs)]:
            try: row[key] = [round(v, 5) for v in Pose_2_Fanuc(fn())]
            except Exception as e: row[key] = str(e)
    if row['type'] == 2:
        for key, fn in [('model_joints', item.Joints), ('tool', item.PoseTool), ('frame', item.PoseFrame), ('limits', item.JointLimits)]:
            try: row[key] = str(fn())
            except Exception as e: row[key] = str(e)
    if row['type'] == ITEM_TYPE_PROGRAM_PYTHON:
        path = out / ('%02d_' % idx + ''.join(c if c not in '<>:"/\\|?*' else '_' for c in row['name']) + '.py')
        try:
            item.Save(str(path))
            data = path.read_bytes()
            row.update(source=str(path), bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
        except Exception as e: row['export_error'] = str(e)
    rows.append(row)
report = {'station': rdk.ActiveStation().Name(), 'run_mode': rdk.RunMode(), 'items': rows}
(out / 'inventory.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
print('REPORT_DIR:', out)
