from pathlib import Path
import ast, json, math, hashlib

root = Path(__file__).resolve().parents[1]
out = root/'sim_scripts/rdk_station_dump/install_v1519_20261103'
out.mkdir(exist_ok=True)
source = (root/'sim_scripts/rdk_station_dump/traj16_continuity_20261103/TCP真实运动_P2P版_15.17_预检同步候选.py').read_text(encoding='utf-8')
tree = ast.parse(source)
function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_validated_records')
ns = {'math': math}
exec(compile(ast.Module(body=[function], type_ignores=[]), 'validate', 'exec'), ns)
records = ns['_validated_records'](json.loads(Path(r'D:/mydata/working things/dobot_arm/RoboDK files 2/连续轨迹16.json').read_text(encoding='utf-8')))
canonical = [dict(type=r['type'], values=[0.0 if abs(float(v)) < 1e-12 else float(v) for v in r['values']],
    singular=bool(r.get('singular', False)), spin360=bool(r.get('spin360', False)), j6_delta=int(r.get('j6_delta', 0))) for r in records]
digest = hashlib.sha256(json.dumps(canonical, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()
baseline = json.loads((root/'sim_scripts/rdk_station_dump/traj16_tcp130_20261103_154825/result.json').read_text(encoding='utf-8'))
helpers = (root/'tools/p2p_v1519_helpers.txt').read_text(encoding='utf-8').replace('__PROFILE_SHA__', digest).replace('__IK_SEEDS__', repr([s['joints'] for s in baseline['plan']]))
source = source.replace("LOG_VERSION = 'v15.17-20261103-预检同步候选'", "LOG_VERSION = 'v15.19-20261103'")
source = source.replace('P2P v15.16', 'P2P v15.19').replace('下次改动 ⇒ v15.16', '下次改动 ⇒ v15.20')
source = source.replace("robot = RDK.Item('', ITEM_TYPE_ROBOT)", "robot = RDK.Item('Dobot CR5', ITEM_TYPE_ROBOT)", 1)
source = source.replace("_ka_robot = _ka_rdk.Item('', ITEM_TYPE_ROBOT)", "_ka_robot = _ka_rdk.Item(robot.Name(), ITEM_TYPE_ROBOT)")
marker = '\ndef _ik_branch_candidates(target_pose, reference):'
assert source.count(marker) == 1
source = source.replace(marker, '\n'+helpers+'\n'+marker)
source = source.replace('solutions = robot.SolveIK_All(_tcp_target_to_flange(target_pose))', 'solutions = _profile_ik_all(_tcp_target_to_flange(target_pose))')
source = source.replace('if robot.SolveIK_All(_tcp_target_to_flange(target)).size(1) == 0:', 'if _profile_ik_all(_tcp_target_to_flange(target)).size(1) == 0:')
source = source.replace('    global _preferred_seed\n', '''    global _preferred_seed, _traj16_profile_active
    _traj16_profile_active = False
    if _traj16_records_match(records):
        if not _controller_body_matches():
            raise RuntimeError('轨迹16连续直线策略要求控制器对齐本体；当前本体参数不符。')
        if not _same_tool_pose(robot.PoseTool(), Fanuc_2_Pose(list(CANONICAL_TOOL))):
            raise RuntimeError('轨迹16连续直线策略要求130mm TCP。')
        if norm(robot.PoseFrame().Pos()) > .01 or pose_angle(robot.PoseFrame()) > math.radians(.01):
            raise RuntimeError('轨迹16连续直线策略要求机器人基座参考系。')
        _traj16_profile_active = True
        log('v15.19：启用已验证轨迹16的校准本体分支搜索；两段直线将在本次预检重新认证。')
''')
source = source.replace('                _verify_obstacle_plan(saved, plan)\n', '                _verify_obstacle_plan(saved, plan)\n                _certify_traj16_direct(plan, log)\n')
source = source.replace("    finally:\n        robot.setJoints(saved)\n        RDK.Render(True)\n\nroot = tk.Tk()", "    finally:\n        _traj16_profile_active = False\n        robot.setJoints(saved)\n        RDK.Render(True)\n\nroot = tk.Tk()")
source = source.replace('movl_direct and i not in MOVL_DIRECT_BLOCK_POINTS', 'movl_direct and _direct_step_allowed(i, step)')
source = source.replace("            _send_q = step['joints']\n            if direct_ready:", "            _send_q = step.get('direct_send_joints', step['joints'])\n            if direct_ready and not step.get('direct_movl_certified'):")
source = source.replace('elif (movl_direct and i in MOVL_DIRECT_BLOCK_POINTS', 'elif (movl_direct and not _direct_step_allowed(i, step)')
needle = '        for i, step in enumerate(plan, 1):\n            for rewind in step[\'rewinds\']:'
source = source.replace(needle, "        log('本次单条MovL动态认证放行点=%s' % [i for i,s in enumerate(plan,1) if s.get('direct_movl_certified')])\n"+needle)
ast.parse(source)
assert source.count('_certify_traj16_direct(plan, log)') == 2
assert "MOVL_DIRECT_BLOCK_POINTS = (9, 11)" in source
target = out/'TCP真实运动_P2P版.py'
target.write_text(source, encoding='utf-8')
(out/'build.json').write_text(json.dumps(dict(profile=digest, source_sha256=hashlib.sha256(target.read_bytes()).hexdigest()), indent=2), encoding='utf-8')
print(target)
