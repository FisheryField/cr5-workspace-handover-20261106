"""Check final receipts and write the reviewable all-segment report."""
from pathlib import Path
import json, hashlib
from robodk.robolink import *
from robodk.robomath import Pose_2_Fanuc
root=Path(__file__).resolve().parents[1]
folder=root/'sim_scripts/rdk_station_dump/install_v1520_20261103'
def latest(pattern):
    p=sorted((root/'sim_scripts/rdk_station_dump').glob(pattern))[-1]
    return p,json.loads(p.read_text(encoding='utf-8'))
path,report=latest('traj16_v1520_installed_*/result.json')
regpath,reg=latest('traj16_v1520_regression_*/result.json')
assert report['result']==reg['result']=='PASS'
assert report['disk_source_matches'] and report['planned_points']==23
assert report['trajectory_unchanged'] and reg['trajectory_unchanged']
assert any('P2将退回72段停走' in line for line in reg['logs'])
assert report['plan'][1]['method']=='MoveJ' and not report['plan'][1]['waypoints']
linear=[i for i,s in enumerate(report['plan'],1) if s['method']=='MoveL']
assert linear==[3,5,8,9,11,13,15,17,19,22]
assert all(s.get('direct_movl_certified') for s in report['plan'] if s.get('waypoints'))
formal=root/'sim_scripts/TCP真实运动_P2P版.py'
assert report['source_sha256']==hashlib.sha256(formal.read_bytes()).hexdigest()
r=Robolink(port=20500)
macro=r.Item('TCP真实运动_P2P版',ITEM_TYPE_PROGRAM_PYTHON)
macro.Save(str((folder/'final_station_readback.py').resolve()))
assert (folder/'final_station_readback.py').read_bytes()==formal.read_bytes()
b=r.Item('Dobot CR5',ITEM_TYPE_ROBOT)
assert abs(b.PoseTool()[2,3]-130)<1e-7
receipt=json.loads((folder/'installation.json').read_text(encoding='utf-8'))
receipt.update(main_precheck=str(path),regression=str(regpath),all_segments_checked=True,
    continuous_linear_endpoints=linear,segmented_execution_points=[],final_tcp=Pose_2_Fanuc(b.PoseTool()))
(folder/'installation.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
rows=['# 轨迹16 v15.20 修复与全段检查','',
    '入口恢复历史成功分支的校准本体逆解；P1→P2 使用一条 MoveJ，不再执行72个途经点。',
    '轨迹文件及130mm TCP未改动；当前站内脚本已更新，旧版保留备份；未覆盖保存 .rdk，未发送实机运动。','',
    '| 相邻点 | 执行方式 | 是否逐途经点停走 |','|---|---|---|']
for n,step in enumerate(report['plan'],1):
    if n==1: continue
    rows.append(f'| P{n-1}→P{n} | 单条 {step["method"]} | 否 |')
rows+=['','验证：主站23点整段碰撞复核通过；10条直线全部通过0.5mm法兰发送路径认证（含数字净化后的实际发送目标、限位、自干涉和落点分支）。',
    '执行函数模拟分派共23条主运动指令；缺失直线认证或关闭直发时，均在发送任何运动前停止。',
    '故障回归：强制优先选择v15.19的错误入口，成功拒绝P2的72段停走方案，切换入口后整段通过。',
    '单条MovL后原有到位检查及必要的MoveJ微纠偏仍保留；未证明驱动断连本身已消除，实机表现仍需测试。','',
    f'主站预检：{path}',f'故障回归：{regpath}',f'SHA256：{receipt["source_sha256"]}']
(folder/'验证报告.md').write_text('\n'.join(rows)+'\n',encoding='utf-8')
r.setRunMode(RUNMODE_RUN_ROBOT)
print('READY v15.20; main=PASS; regression=PASS; linear=10; segmented=0; no motion sent')
