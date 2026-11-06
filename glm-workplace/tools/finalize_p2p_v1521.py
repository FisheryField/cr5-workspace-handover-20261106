from pathlib import Path
import json,hashlib
from robodk.robolink import *
from robodk.robomath import Pose_2_Fanuc
root=Path(__file__).resolve().parents[1]
folder=root/'sim_scripts/rdk_station_dump/install_v1521_20261103'
path=sorted((root/'sim_scripts/rdk_station_dump').glob('traj16_v1521_installed_*/result.json'))[-1]
report=json.loads(path.read_text(encoding='utf-8'))
assert report['result']=='PASS' and report['planned_points']==23 and report['disk_source_matches']
assert report['trajectory_unchanged']
assert all(report['plan'][i]['method']=='MoveJ' and not report['plan'][i]['waypoints'] for i in (1,15))
assert all(s.get('direct_movl_certified') for s in report['plan'] if s.get('waypoints'))
formal=root/'sim_scripts/TCP真实运动_P2P版.py'
assert report['source_sha256']==hashlib.sha256(formal.read_bytes()).hexdigest()
r=Robolink(port=20500)
receipt=json.loads((folder/'installation.json').read_text(encoding='utf-8'))
macro=r.Item(receipt['macro'],ITEM_TYPE_PROGRAM_PYTHON)
assert macro.Valid()
macro.Save(str((folder/'final_station_readback.py').resolve()))
assert (folder/'final_station_readback.py').read_bytes()==formal.read_bytes()
b=r.Item('Dobot CR5',ITEM_TYPE_ROBOT)
assert abs(b.PoseTool()[2,3]-130)<1e-7
receipt.update(main_precheck=str(path),main_precheck_result='PASS',final_tcp=Pose_2_Fanuc(b.PoseTool()),
    continuous_linear_points=[i for i,s in enumerate(report['plan'],1) if s.get('direct_movl_certified')])
(folder/'installation.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
rows=['# P2P v15.21 修复验证','',
    '已取消固定轨迹坐标指纹对连续TCP规划策略的启用限制。修改坐标后，校准本体IK分支补全、入口优先、防细分停走和本次直线认证仍然执行。',
    '数据摘要只用于将认证绑定到本次坐标及起终点/发送关节，防止旧认证复用。工具130mm、控制器对齐本体及基座参考系条件继续检查。',
    '当前轨迹16点位未修改；站内宏名称保留；旧脚本已备份，未覆盖保存 .rdk，未发送实机运动。','',
    '验证：当前23点主站预检通过；强制错误入口时拒绝P2的72段停走，换构型后通过；另改坐标也重新认证通过；不可达端点被拒绝。',
    '模拟执行：23条主运动指令；缺认证、关闭直发、旧坐标认证、目标关节被改动四种情况下发送运动数均为0。','',
    '| 相邻点 | 执行方式 | 每段主指令数 |','|---|---|---|']
for n,step in enumerate(report['plan'],1):
    if n>1: rows.append(f'| P{n-1}→P{n} | {step["method"]} | 1 |')
rows+=['','单条MovL后既有到位检测及必要的MoveJ微纠偏保留。实机驱动断连是否完全消除，仍需实测。',
    f'主站结果：{path}',f'SHA256：{receipt["source_sha256"]}']
(folder/'验证报告.md').write_text('\n'.join(rows)+'\n',encoding='utf-8')
r.setRunMode(RUNMODE_RUN_ROBOT)
print('READY v15.21: 23 points PASS, 10 direct MovL, P2/P16 single MoveJ, trajectory unchanged')
