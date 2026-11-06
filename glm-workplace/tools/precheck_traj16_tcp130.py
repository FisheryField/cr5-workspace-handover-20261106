"""Check a temporary +Z130 TCP; restore the original linked tool afterwards."""
from pathlib import Path
import sys
runner = Path(__file__).with_name('precheck_traj16_current.py')
code = runner.read_text(encoding='utf-8')
code = code.replace('RUNMODE_SIMULATE\n', 'RUNMODE_SIMULATE, ITEM_TYPE_TOOL\n')
code = code.replace('from robodk.robomath import Pose_2_Fanuc', 'from robodk.robomath import Pose_2_Fanuc, Fanuc_2_Pose')
code = code.replace("'traj16_precheck_'", "'traj16_tcp130_'")
code = code.replace("    assert abs(tool[2,3] - 126) < 1e-6, 'Active TCP is not 126mm; do not silently use a different tool'", """    original_link = robot.getLink(ITEM_TYPE_TOOL)
    temporary_tool = robot.AddTool(Fanuc_2_Pose([0, 0, 130, 0, 0, 0]), '_offline_TCP130_test')
    robot.setPoseTool(temporary_tool)
    report['tested_tool'] = Pose_2_Fanuc(robot.PoseTool())
    print('TESTED_TOOL', report['tested_tool'], flush=True)
""")
code = code.replace('    robot.setJoints(saved_joints)\n', """    if 'temporary_tool' in globals():
        if original_link.Valid():
            robot.setPoseTool(original_link)
        else:
            robot.setPoseTool(tool)
        temporary_tool.Delete()
    robot.setJoints(saved_joints)
""")
code = code.replace('    rdk.Render(True)\n', "    rdk.Render(True)\n    rdk.Command('Trace', 'On')\n")
sys.argv.append('--start-zero')
exec(compile(code, str(runner), 'exec'), dict(__file__=str(runner), __name__='__main__'))
