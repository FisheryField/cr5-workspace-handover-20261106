"""Test the Y-3 candidate with both stroke endpoints shortened to X +/-100."""
from pathlib import Path
import socket,time
for attempt in range(100):
    try:
        with socket.create_connection(('127.0.0.1',20501),timeout=.2):
            break
    except OSError:
        time.sleep(.2)
else:
    raise RuntimeError('Isolated RoboDK port 20501 did not start')
source=Path(__file__).with_name('check_traj16_yminus3.py').read_text(encoding='utf-8')
source=source.replace("'traj16_yminus3_'", "'traj16_yminus3_x100_'")
source=source.replace("('paired_P8_P11',[8,9,10,11])", "('paired_P8_P11_X100',[8,9,10,11])")
needle="        for n in points: candidate[n-1]['values'][1]-=3.0"
assert source.count(needle)==1
source=source.replace(needle,"""        assert all(abs(original[n-1]['values'][1]+681.5)<1e-6 for n in points)
        for n in points: candidate[n-1]['values'][1]-=3.0
        candidate[8]['values'][0]=-100.0
        candidate[9]['values'][0]=-100.0
        candidate[10]['values'][0]=100.0""")
source=source.replace('sim=Robolink(port=20501)', 'sim=Robolink(port=20501)\nassert sim.PORT==20501')
exec(compile(source,str(Path(__file__).with_name('check_traj16_yminus3.py')),'exec'))
