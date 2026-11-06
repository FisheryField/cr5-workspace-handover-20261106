from pathlib import Path
import ast, types
p=Path('sim_scripts/TCP真实运动_P2P版.py')
s=p.read_text(encoding='utf-8').replace('v15.15','v15.16')
s=s.replace('def _wait_arrival_then_static(', 'class ControllerMotionFault(RuntimeError):\n    """A controller state that must never trigger a motion resend."""\n    pass\n\n\ndef _wait_arrival_then_static(',1)
start=s.index('def _try_set_tool_user():')
end=s.index('\ndef _movl_digit_safe_joints',start)
s=s[:start]+'''def _try_set_tool_user():
    """Unsupported through this driver: RunCodeCustom becomes RunScript, not raw Tool/User."""
    raise ControllerMotionFault('当前驱动未验证Tool/User透传；禁止通过项目调用设置坐标系。')

'''+s[end:]
s=s.replace("log('  ⚠️ Tool(0)/User(0) 下发不完整，仍继续直发（记录以便判读）')", "raise ControllerMotionFault('Tool/User未确认，停止直发。')")
s=s.replace("                _single_move_settle('MoveL', _send_pose, require_joints=False,", "                log('P%d：发送法兰目标=%s；认证关节=%s；TCP=%s' % (i, Pose_2_Fanuc(_send_pose), step['joints'], Pose_2_Fanuc(robot.PoseTool())))\n                _single_move_settle('MoveL', _send_pose, require_joints=False,")
tree=ast.parse(s)
names={'ControllerMotionFault','_wait_arrival_then_static','_try_set_tool_user'}
nodes=[n for n in tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in names]
ns=dict(time=types.SimpleNamespace(time=lambda:0),log=lambda m:None,MOVL_ARRIVE_TOL_DEG=5,MOVL_ARRIVE_WAIT_S=60)
exec(compile(ast.Module(body=nodes,type_ignores=[]),'<offline-tests>','exec'),ns)
ns['_controller_feedback']=lambda:([0]*6,[0]*6,9)
try:
    ns['_wait_arrival_then_static']([10]*6)
    raise AssertionError('Fault accepted')
except ns['ControllerMotionFault']:
    pass
ns['_controller_feedback']=lambda:([10]*6,[0]*6,5)
assert ns['_wait_arrival_then_static']([10]*6)==([10]*6,True)
try:
    ns['_try_set_tool_user']()
    raise AssertionError('Unsupported tool setting accepted')
except ns['ControllerMotionFault']:
    pass
p.write_text(s,encoding='utf-8')
print('PASS: alarm fails immediately; arrival accepted; unsupported Tool/User stops; no hardware calls')
