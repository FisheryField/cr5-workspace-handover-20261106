"""Offline-only direction/width comparison; keep the original trajectory untouched."""
from pathlib import Path
runner=Path(__file__).with_name('tune_traj16_tcp130.py')
s=runner.read_text(encoding='utf-8')
s=s.replace('traj16_tcp130_20261029_150821','traj16_tcp130_20261103_150928')
s=s.replace("'traj16_tune130_'", "'traj16_direction_width_'")
s=s.replace("assert hashlib.sha256(source.read_bytes()).hexdigest() == baseline['source_sha256']", "assert source.read_bytes() == (base/'sim_scripts/TCP真实运动_P2P版.py').read_bytes()")
s=s.replace("    temporary = robot.AddTool", "    rdk.setRunMode(RUNMODE_SIMULATE)\n    temporary = robot.AddTool")
start=s.index("    for label, changes in [")
end=s.index("        validated =",start)
s=s[:start]+'''    for label, xs in [('direction_only',(120,120,-120)), ('width_only',(-100,-100,100)), ('old_direction_width',(100,100,-100))]:
        candidate = copy.deepcopy(records)
        for point, x in zip((9,10,11), xs):
            candidate[point-1]['values'][0] = x
        changes = (9,10,11)
        assert all(rec == records[i] for i,rec in enumerate(candidate) if i+1 not in changes)
'''+s[end:]
s=s.replace("entry.update(result='PASS',plan=plan,metrics=metrics(plan))", """entry.update(result='PASS',plan=plan,metrics=metrics(plan),
                         critical_joints={str(i):plan[i-1]['joints'] for i in (8,9,10,11)},
                         min_abs_j3_critical_deg=min(abs(q[2]) for step in plan[7:11] for q in (step.get('waypoints') or [step['joints']])))""")
exec(compile(s,str(runner),'exec'),dict(__file__=str(runner),__name__='__main__'))
