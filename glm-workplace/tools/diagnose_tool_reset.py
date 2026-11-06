"""Probe TCP selection semantics without connecting to or moving hardware."""
import io, sys, json
from robodk.robolink import Robolink, ITEM_TYPE_ROBOT, ITEM_TYPE_TOOL
from robodk.robomath import transl, eye, Pose_2_Fanuc
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
rdk = Robolink(port=20500)
robot = rdk.Item('', ITEM_TYPE_ROBOT)
def report(label):
    link = robot.getLink(ITEM_TYPE_TOOL)
    print(label, json.dumps({'tcp': Pose_2_Fanuc(robot.PoseTool()),
          'active_tool': link.Name() if link.Valid() else None,
          'tools': [{'name': t.Name(), 'tcp': Pose_2_Fanuc(t.PoseTool())}
                    for t in robot.Childs() if t.Type() == ITEM_TYPE_TOOL]}, ensure_ascii=False))
report('INITIAL')
original_pose = robot.PoseTool()
original_link = robot.getLink(ITEM_TYPE_TOOL)
probe = None
try:
    robot.setPoseTool(transl(0, 0, 126))
    report('MATRIX_126')
    other = Robolink(port=20500)
    print('NEW_API_CONNECTION_TCP', Pose_2_Fanuc(other.Item('', ITEM_TYPE_ROBOT).PoseTool()))
    other.Disconnect()
    probe = robot.AddTool(transl(0, 0, 126), '_TCP_RESET_DIAGNOSTIC_TEMP')
    robot.setPoseTool(probe)
    report('ITEM_126')
    robot.setPoseTool(eye(4))
    report('IDENTITY_MATRIX_WHILE_TOOL_LINKED')
    robot.setPoseTool(probe)
    report('RESTORE_LINK_ONLY')
finally:
    robot.setPoseTool(original_link if original_link.Valid() else original_pose)
    if probe is not None: probe.Delete()
report('RESTORED_INITIAL')
