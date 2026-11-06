from pathlib import Path
import ast,re
root=Path(__file__).resolve().parents[1]
folder=root/'sim_scripts/rdk_station_dump/install_v1521_20261103'
folder.mkdir(exist_ok=True)
s=(root/'sim_scripts/TCP真实运动_P2P版.py').read_text(encoding='utf-8')
assert "v15.20-20261103" in s
s=s.replace('v15.20','v15.21').replace('_traj16_profile_active','_continuous_profile_active')
s=s.replace('TRAJ16_IK_SEEDS','CALIBRATED_IK_SEEDS')
s=s.replace("# v15.21: only this exact trajectory gets calibrated-model branch recovery\n# and freshly certified single-MovL strokes. Other records keep legacy policy.\n", "# Continuous TCP paths always recover calibrated-body IK branches and re-certify\n# their actual command paths. Record hashes bind receipts, never enable policy.\n")
s=re.sub(r"^TRAJ16_PROFILE_SHA256 = '[^']+'\n",'',s,flags=re.M)
s=s.replace('def _traj16_records_match(records):','def _records_fingerprint(records):')
s=s.replace("separators=(',', ':')).encode('utf-8')).hexdigest() == TRAJ16_PROFILE_SHA256", "separators=(',', ':')).encode('utf-8')).hexdigest()")
s=s.replace('if _traj16_records_match(records):','if _continuous_records(records):')
needle='def _controller_body_matches():'
helper='''def _continuous_records(records):
    return len(records) > 1 and any(r.get('type') == 'TCP' for r in records)


def _assert_continuous_dispatch(records, initial, plan, direct_enabled):
    if not _continuous_records(records):
        return
    fingerprint = _records_fingerprint(records)
    previous = initial
    for number, step in enumerate(plan, 1):
        if step.get('waypoints'):
            certificate = step.get('direct_certificate') or {}
            if (step['method'] != 'MoveL' or not step.get('direct_movl_certified')
                    or certificate.get('records_sha256') != fingerprint
                    or certificate.get('start_joints') != list(previous)
                    or certificate.get('end_joints') != step['joints']
                    or certificate.get('send_joints') != step.get('direct_send_joints')):
                raise RuntimeError(f'P{number}缺少与当前数据及构型一致的连续直线认证，禁止退回逐点停走。')
            if not direct_enabled:
                raise RuntimeError('连续TCP轨迹需要单条MovL模式，禁止退回细分停走。')
        previous = step['joints']


'''
assert s.count(needle)==1
s=s.replace(needle,helper+needle)
a=s.index('        if _continuous_records(records):\n',s.index("log('本次单条MovL动态认证放行点="))
b=s.index('        for i, step in enumerate(plan, 1):',a)
s=s[:a]+"        _assert_continuous_dispatch(records, start, plan, movl_direct)\n"+s[b:]
s=s.replace('def _certify_traj16_direct(plan, log):', 'def _certify_continuous_direct(records, initial, plan, log):')
s=s.replace('_certify_traj16_direct(plan, log)', '_certify_continuous_direct(records, saved, plan, log)')
s=s.replace("            start = plan[number-2]['joints']", "            start = initial if number == 1 else plan[number-2]['joints']")
s=s.replace("dict(profile=TRAJ16_PROFILE_SHA256,\n                    samples=", "dict(records_sha256=_records_fingerprint(records),\n                    start_joints=list(start), end_joints=list(step['joints']), send_joints=list(send_q),\n                    samples=")
s=s.replace('轨迹16连续直线策略','连续TCP轨迹策略').replace('轨迹16单条MovL','连续TCP单条MovL')
s=s.replace('启用已验证轨迹16的校准本体分支搜索；两段直线将在本次预检重新认证。',
    '启用校准本体分支搜索及防停走检查；不依赖旧坐标指纹，全部直线按当前数据重新认证。')
s=s.replace('连续运动（P2P v15.21）：短直线段(≤210mm/姿态恒定)强制 MoveL 直走；前视选解+绑定执行；弧碰退回 MoveL 细分（步长20mm）；死路分支救援+避障选解；换向自动换向/回绕/切分支；首点种子枚举+整段重试；法兰补偿MOVL 默认开；规划与预检不变。',
    '连续运动（P2P v15.21）：修改点位后仍启用分支搜索、防停走及逐段重新认证；无法认证的直线在发送运动前停止；130mm TCP。')
s=s.replace('下次改动 ⇒ v15.21','下次改动 ⇒ v15.22')
assert '_traj16_records_match' not in s and 'TRAJ16_PROFILE_SHA256' not in s
ast.parse(s)
(folder/'TCP真实运动_P2P版.py').write_text(s,encoding='utf-8')
print(folder)
