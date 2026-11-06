from pathlib import Path
import ast
p = Path('sim_scripts/TCP真实运动_P2P版.py')
s = p.read_text(encoding='utf-8')
s = s.replace("LOG_VERSION = 'v15.10-20261103'", "LOG_VERSION = 'v15.11-20261103'")
s = s.replace('CANONICAL_TOOL = (0.0, 0.0, 126.0,', 'CANONICAL_TOOL = (0.0, 0.0, 130.0,')
s = s.replace("TCP_TOOL_NAME = 'CR5_TCP_126mm'", "TCP_TOOL_NAME = 'CR5_TCP_130mm'")
s = s.replace('已自动恢复 [0,0,126]', '已自动恢复 [0,0,130]')
s = s.replace('P2P v15.10', 'P2P v15.11')
s = s.replace('def _require_joints(expected, _tries=3, _allow_fix=True):', 'def _require_joints(expected, _tries=3, _allow_fix=False):')
s = s.replace('        return _settle_core(method, target, require_joints, expect_target, True, _retry)', '''        result = _settle_core(method, target, require_joints, expect_target, True, _retry)
        # Synchronize measured joints before restoring the tool and visible mesh.
        actual, is_static = _wait_controller_static()
        if not is_static:
            raise RuntimeError('法兰直发后未确认静止，停止后续命令。')
        robot.setJoints(actual)
        return result''')
s = s.replace("robot.setJoints(step['joints'])   # v14w39：模型钉到认证终点，清本地动画残留态", "robot.setJoints(_post)   # 显示实测姿态，不用预期目标掩盖未到位。")
needle = '            elif waypoints:\n'
assert s.count(needle)==1
s = s.replace(needle, '''                if not waypoints:
                    raise RuntimeError(f'P{i}：禁直发点缺少途经点，停止。')
                for way in waypoints:
                    _move_with_completion_check('MoveJ', way, False)
                    _require_joints(way)
                _require_joints(step['joints'])
            elif waypoints:
''')
tree = ast.parse(s)
branch = next(n for n in ast.walk(tree) if isinstance(n,ast.If) and 'i in MOVL_DIRECT_BLOCK_POINTS' in ast.unparse(n.test))
calls=[]
ns=dict(movl_direct=True,i=9,MOVL_DIRECT_BLOCK_POINTS=(9,),seg_mm=120,MOVL_DIRECT_MAX_MM=210,seg_rot=0,
        math=__import__('math'),waypoints=[[1]*6,[2]*6],step={'joints':[2]*6},log=lambda m:None,
        _move_with_completion_check=lambda *a:calls.append(a),_require_joints=lambda q:None)
exec(compile(ast.Module(body=branch.body,type_ignores=[]),'<blocked-point-test>','exec'),ns)
assert calls==[('MoveJ',[1]*6,False),('MoveJ',[2]*6,False)]
ns['waypoints']=[]
try:
    exec(compile(ast.Module(body=branch.body,type_ignores=[]),'<empty-test>','exec'),ns)
    raise AssertionError('Missing waypoints accepted')
except RuntimeError:
    pass
p.write_text(s,encoding='utf-8')
print('PASS: syntax; blocked P9 executes each waypoint; missing waypoints stops. Saved v15.11.')
