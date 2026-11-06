"""Profile the existing offline-only runner, without hardware access."""
from pathlib import Path
import sys

runner = Path(__file__).with_name('precheck_traj16_current.py')
code = runner.read_text(encoding='utf-8')
code = code.replace('import io, sys, json, hashlib, datetime, traceback',
                    'import io, sys, json, hashlib, datetime, traceback, cProfile, pstats, time')
code = code.replace("'traj16_precheck_'", "'traj16_profile_'")
code = code.replace("    plan = ns['_plan_continuous_trajectory'](records, 500.0, log)", """    profiler = cProfile.Profile()
    started = time.perf_counter()
    profiler.enable()
    try:
        plan = ns['_plan_continuous_trajectory'](records, 500.0, log)
    finally:
        profiler.disable()
        report['planner_seconds'] = time.perf_counter() - started
        profiler.dump_stats(str(out/'planner.prof'))
        with (out/'profile.txt').open('w', encoding='utf-8') as stream:
            pstats.Stats(profiler, stream=stream).sort_stats('cumulative').print_stats(70)
        print('PLANNER_SECONDS', report['planner_seconds'], flush=True)
""")
code = code.replace("    rdk.Render(True)\n", "    rdk.Render(True)\n    rdk.Command('Trace', 'On')\n")
sys.argv.append('--start-zero')
exec(compile(code, str(runner), 'exec'), dict(__file__=str(runner), __name__='__main__'))
