"""Compare cold/warm offline plans against the measured baseline."""
from pathlib import Path
runner = Path(__file__).with_name('precheck_traj16_current.py')
code = runner.read_text(encoding='utf-8')
code = code.replace('import io, sys, json, hashlib, datetime, traceback',
                    'import io, sys, json, hashlib, datetime, traceback, time')
code = code.replace("'traj16_precheck_'", "'traj16_speed_verify_'")
code = code.replace('macros[0].Save(str(source))',
                    "source.write_bytes((base/'sim_scripts'/'TCP真实运动_P2P版.py').read_bytes())")
code = code.replace("    plan = ns['_plan_continuous_trajectory'](records, 500.0, log)", """    baseline = json.loads((base/'sim_scripts/rdk_station_dump/traj16_profile_20261027_154956/result.json').read_text(encoding='utf-8'))
    assert report['trajectory_sha256'] == baseline['trajectory_sha256']
    report['timings'] = []
    for label in ('cold', 'warm'):
        robot.setJoints(joints)
        started = time.perf_counter()
        plan = ns['_plan_continuous_trajectory'](records, 500.0, log)
        elapsed = time.perf_counter() - started
        assert plan == baseline['plan'], label + ' plan changed'
        report['timings'].append(dict(run=label, seconds=elapsed, identical_plan=True))
        print('TIMING', label, elapsed, 'IDENTICAL_PLAN', flush=True)
""")
code = code.replace("    rdk.Render(True)\n", "    rdk.Render(True)\n    rdk.Command('Trace', 'On')\n")
import sys
sys.argv.append('--start-zero')
exec(compile(code, str(runner), 'exec'), dict(__file__=str(runner), __name__='__main__'))
