"""Force the v15.19 bad entry first; require rejection and a new safe branch."""
from pathlib import Path
source=Path('tools/precheck_v1520.py').read_text(encoding='utf-8')
source=source.replace("'traj16_v1520_check_'", "'traj16_v1520_regression_'")
needle="    plan = ns['_plan_continuous_trajectory'](records, 500.0, log)"
assert source.count(needle)==1
source=source.replace(needle,"""    original_lazy = ns['_lazy_valid_seeds']
    def force_bad_entry_first(seeds, start):
        wrong=min(seeds,key=lambda s:sum((a-b)**2 for a,b in zip(s,
            [16.613876,-3.710556,-66.327044,-20.134456,89.713880,-73.631240])))
        return original_lazy([wrong]+[s for s in seeds if s!=wrong],start)
    ns['_lazy_valid_seeds']=force_bad_entry_first
"""+needle+"""
    assert any('P2将退回72段停走' in line for line in logs),logs
    assert plan[1]['method']=='MoveJ' and not plan[1]['waypoints']
""")
exec(compile(source,str(Path('tools/precheck_v1520.py').resolve()),'exec'))
