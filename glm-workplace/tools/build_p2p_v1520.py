from pathlib import Path
import ast

root = Path(__file__).resolve().parents[1]
out = root/'sim_scripts/rdk_station_dump/install_v1520_20261103'
out.mkdir(exist_ok=True)
src = (root/'sim_scripts/TCP真实运动_P2P版.py').read_text(encoding='utf-8')
assert "LOG_VERSION = 'v15.19" in src or 'v15.19-20261103' in src
src = src.replace('v15.19', 'v15.20')
needle = "            seeds.sort(key=lambda s: _obstacle_posture_key(s, saved))"
assert src.count(needle) == 1
src = src.replace(needle, needle + '''
            if _traj16_profile_active:
                # Recover the previously successful entry branch on this calibrated body.
                # These are IK seeds, never executable joint targets.
                entry = robot.SolveIK(_tcp_target_to_flange(
                    fanuc_values_to_pose(*first_tcp['values'])), TRAJ16_IK_SEEDS[0]).list()
                if len(entry) == 6:
                    seeds.sort(key=lambda s: sum((a-b)**2 for a,b in zip(s, entry)))
                log('v15.20：优先历史成功入口分支；任何细分停走退化均重新选解或停止预检。')''')
needle = "        for number in (9, 11):\n            step = plan[number-1]"
assert src.count(needle) == 1
src = src.replace(needle, "        for number, step in enumerate(plan, 1):\n            if step['method'] != 'MoveL':\n                continue")
needle = "            start = plan[number-2]['joints']\n            send_q, note"
assert src.count(needle) == 1
src = src.replace(needle, "            start = plan[number-2]['joints']\n            relative = _trajectory_pose(step['joints']) * invH(_trajectory_pose(start))\n            if norm(relative.Pos()) > MOVL_DIRECT_MAX_MM or pose_angle(relative) > math.radians(.5):\n                raise ValueError(f'P{number}将退回{len(step[\"waypoints\"])}段停走，换入口分支重试。')\n            send_q, note")
needle = "                log('逐段规划完成，开始整段碰撞复核（1mm/1°采样，请稍候）…')"
assert src.count(needle) == 1
src = src.replace(needle, '''                if _traj16_profile_active:
                    previous = saved
                    for number, step in enumerate(plan, 1):
                        if step.get('waypoints'):
                            rel = _trajectory_pose(step['joints']) * invH(_trajectory_pose(previous))
                            if (step['method'] != 'MoveL' or norm(rel.Pos()) > MOVL_DIRECT_MAX_MM
                                    or pose_angle(rel) > math.radians(.5)):
                                raise ValueError(f'P{number}将退回{len(step["waypoints"])}段停走，换入口分支重试。')
                        previous = step['joints']
''' + needle)
needle = "        for i, step in enumerate(plan, 1):\n            for rewind in step['rewinds']:"
assert src.count(needle) == 1
src = src.replace(needle, '''        if _traj16_records_match(records):
            for number, step in enumerate(plan, 1):
                if step.get('waypoints') and not step.get('direct_movl_certified'):
                    raise RuntimeError(f'P{number}缺少本次连续直线认证，禁止退回逐点停走。')
            if not movl_direct:
                raise RuntimeError('轨迹16需要单条MovL模式，禁止退回细分停走。')
''' + needle)
ast.parse(src)
(out/'TCP真实运动_P2P版.py').write_text(src, encoding='utf-8')
print(out)
