"""Mock hardware and exercise production dispatch, including stale receipts."""
from pathlib import Path
source=Path(__file__).with_name('test_v1520_dispatch.py').read_text(encoding='utf-8')
source=source.replace('v1520','v1521').replace('v15.20','v15.21')
source=source.replace("report = json.loads(reports[-1].read_text(encoding='utf-8'))", "report = json.loads(reports[-1].read_text(encoding='utf-8'))[0]")
source=source.replace("assert report['result'] == 'PASS' and report['version']=='v15.21-20261103'", "assert report['result']=='PASS' and report['case']=='current'")
source=source.replace("Path(report['file'])", "Path(report['candidate_file'])")
source=source.replace("('normal', 'missing_certificate', 'direct_disabled')", "('normal', 'missing_certificate', 'direct_disabled', 'stale_coordinates', 'changed_target')")
source=source.replace("        plan=copy.deepcopy(report['plan'])", """        plan=copy.deepcopy(report['plan'])
        case_data=copy.deepcopy(data)
        if case=='stale_coordinates': case_data[7]['values'][1]+=.1
        if case=='changed_target': plan[2]['joints'][0]+=.1""")
source=source.replace("ns['_execute_checked_real'](data)", "ns['_execute_checked_real'](case_data)")
exec(compile(source,str(Path(__file__).with_name('test_v1520_dispatch.py')),'exec'))
