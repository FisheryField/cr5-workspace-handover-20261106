"""Run current and edited trajectories without special profile registration."""
from pathlib import Path
import socket,time
for attempt in range(100):
    try:
        with socket.create_connection(('127.0.0.1',20501),timeout=.2): break
    except OSError: time.sleep(.2)
else: raise RuntimeError('Isolated RoboDK port 20501 did not start')
source=Path(__file__).with_name('check_traj16_yminus3.py').read_text(encoding='utf-8')
source=source.replace("'traj16_yminus3_'", "'traj16_v1521_check_'")
source=source.replace("code=source.read_text(encoding='utf-8').split('root = tk.Tk()')[0]",
    "code=(root/'sim_scripts/rdk_station_dump/install_v1521_20261103/TCP真实运动_P2P版.py').read_text(encoding='utf-8').split('root = tk.Tk()')[0]")
source=source.replace("assert 'v15.20-20261103' in code", "assert 'v15.21-20261103' in code")
source=source.replace('sim=Robolink(port=20501)', 'sim=Robolink(port=20501)\nassert sim.PORT==20501')
source=source.replace("[('paired_P8_P11',[8,9,10,11])]", "[('current',[8,9,10,11]),('edited_after_current',[8,9,10,11]),('unreachable',[8,9,10,11])]")
source=source.replace("        for n in points: candidate[n-1]['values'][1]-=3.0", """        if case=='edited_after_current':
            for n in points: candidate[n-1]['values'][1]=-684.5
            candidate[7]['values'][0]=100.0
            candidate[8]['values'][0]=candidate[9]['values'][0]=-100.0
            candidate[10]['values'][0]=100.0
        elif case=='unreachable':
            for n in points: candidate[n-1]['values'][1]=-685.5
            candidate[8]['values'][0]=candidate[9]['values'][0]=-120.0
            candidate[10]['values'][0]=120.0""")
a=source.index("        production_match=ns['_traj16_records_match'](records)")
b=source.index('        logs=[]',a)
source=source[:a]+"        test_hash=ns['_records_fingerprint'](records)\n        production_match=None\n"+source[b:]
source=source.replace("script_sha256=hashlib.sha256(source.read_bytes()).hexdigest()", "script_sha256=hashlib.sha256((root/'sim_scripts/rdk_station_dump/install_v1521_20261103/TCP真实运动_P2P版.py').read_bytes()).hexdigest()")
source=source.replace("            plan=ns['_plan_continuous_trajectory'](records,500.0,log)", """            if case=='current':
                original_lazy=ns['_lazy_valid_seeds']
                def bad_first(seeds,start):
                    wrong=min(seeds,key=lambda s:sum((a-b)**2 for a,b in zip(s,
                        [16.613876,-3.710556,-66.327044,-20.134456,89.713880,-73.631240])))
                    return original_lazy([wrong]+[s for s in seeds if s!=wrong],start)
                ns['_lazy_valid_seeds']=bad_first
            plan=ns['_plan_continuous_trajectory'](records,500.0,log)
            if case=='current':
                assert any('P2将退回72段停走' in line for line in logs)
            assert plan[1]['method']=='MoveJ' and not plan[1]['waypoints']
            assert plan[15]['method']=='MoveJ' and not plan[15]['waypoints']
            ns['_assert_continuous_dispatch'](records,[0]*6,plan,True)""")
exec(compile(source,str(Path(__file__).with_name('check_traj16_yminus3.py')),'exec'))
