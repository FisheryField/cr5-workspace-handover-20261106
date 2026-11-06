# -*- coding: utf-8 -*-
"""结构复现：宏 v12 死因二分。
复刻宏的完整运行结构（tkinter 主线程内同步预检 + 独立Robolink保活线程 + 30004只读反馈），
自动触发、纯仿真+只读，零运动指令。若进程死亡 -> 逐项关闭结构二分定位。
"""
import io, os, sys, time, math, socket, struct, threading, queue

MODE = sys.argv[1] if len(sys.argv) > 1 else 'full'   # full | nokeepalive | notk | nosock
HLOG = r'D:\mydata\glm-workplace\sim_scripts\repro_struct_log.txt'
CRASH = r'D:\mydata\glm-workplace\sim_scripts\repro_struct_crash.txt'

def hlog(s):
    with io.open(HLOG, 'a', encoding='utf-8') as f:
        f.write(time.strftime('%H:%M:%S') + ' | [' + MODE + '] ' + s + '\n')

try:
    import faulthandler as _fh
    _fh.enable(CRASH, all_threads=True)
except Exception:
    pass

hlog('===== struct repro start pid=%d argv=%r' % (os.getpid(), sys.argv))

hlog('import robodk + tkinter')
from robodk.robolink import Robolink, ITEM_TYPE_ROBOT, ITEM_TYPE_OBJECT, ITEM_TYPE_TOOL, RUNMODE_SIMULATE, RUNMODE_RUN_ROBOT, COLLISION_ON, COLLISION_OFF, ROBOTCOM_READY
from robodk.robomath import Fanuc_2_Pose, invH
import tkinter as tk

hlog('Robolink()')
RDK = Robolink()
robot = RDK.Item('', ITEM_TYPE_ROBOT)
hlog('robot=%s valid=%s' % (robot.Name(), robot.Valid()))

FB_MARK = b'\x5A\xA5\x0F\x00'   # 30004 反馈帧 marker（已核：帧1440字节，marker@48）
FB_IP, FB_PORT = '192.168.5.1', 30004

def read_feedback_once():
    s = socket.create_connection((FB_IP, FB_PORT), timeout=3)
    s.settimeout(2)
    try:
        buf = b''
        t0 = time.time()
        while len(buf) < 1440 * 2 and time.time() - t0 < 3:
            chunk = s.recv(4096)
            if not chunk:
                break
            buf += chunk
        i = buf.find(FB_MARK, max(0, len(buf) - 1440 - 16))
        if i >= 0 and len(buf) - i >= 448:
            q = list(struct.unpack_from('<6d', buf, i + 192))
            return q
        return None
    finally:
        s.close()

def driver_keepalive(stop_ev, tag):
    ka_rdk = Robolink()
    ka_robot = ka_rdk.Item('', ITEM_TYPE_ROBOT)
    n = 0
    while not stop_ev.wait(2.0):
        n += 1
        try:
            st, m = ka_robot.ConnectedState()
            hlog('keepalive#%d(%s) ConnectedState=%s' % (n, tag, st))
        except Exception as e:
            hlog('keepalive#%d(%s) exc=%r' % (n, tag, e))

start = [16.38, -34.90, -44.95, 169.85, -90.00, 106.38]
vals = [0.0, -775.0, 300.0, -90.0, 0.0, 180.0]

def run_precheck():
    hlog('进入 run_precheck（主线程）')
    RDK.setRunMode(RUNMODE_SIMULATE)
    RDK.Command('Trace', 'Off')
    robot.setJoints(start)
    for name in ('安装台_650x650x80mm', '地面_禁止穿越', '磨砂圆柱_R180_H40'):
        obstacle = RDK.Item(name, ITEM_TYPE_OBJECT)
        if not obstacle.Valid():
            continue
        if name == '安装台_650x650x80mm':
            RDK.setCollisionActivePair(COLLISION_OFF, robot, obstacle, 0, 0)
        for link in range(1, 7):
            RDK.setCollisionActivePair(COLLISION_ON, robot, obstacle, link, 0)
    RDK.setCollisionActive(COLLISION_ON)
    hlog('障碍配置完成')
    st = robot.MoveJ_Test(start, start, minstep_deg=1)
    hlog('MoveJ_Test(start,start)=%s' % st)
    target = Fanuc_2_Pose(list(vals))
    st = robot.MoveL_Test(start, target, minstep_mm=10)
    hlog('MoveL_Test 10mm=%s' % st)
    if st == 0:
        st = robot.MoveL_Test(start, target, minstep_mm=1)
        hlog('MoveL_Test 1mm=%s' % st)
    if st != 0:
        hlog('线性不可行，进入MoveJ兜底（宏同款）')
        lower, upper, _ = robot.JointLimits()
        lower, upper = lower.list(), upper.list()
        sols = robot.SolveIK_All(target)
        sol_list = [list(map(float, sol[:6])) for sol in sols.rows]
        candidates = []
        for solution in sol_list:
            q = [((float(v) + 180.0) % 360.0) - 180.0 for v in solution[:6]]
            for turns6 in (0, -1, 1):
                cand = q[:]
                cand[5] += 360.0 * turns6
                if all(lower[j] <= cand[j] <= upper[j] for j in range(6)):
                    if not any(max(abs(a - b) for a, b in zip(cand, old)) < 1e-6 for old in candidates):
                        candidates.append(cand)
        hlog('候选 %d 个' % len(candidates))
        found = None
        for idx, end in enumerate(candidates):
            st = robot.MoveJ_Test(start, end, minstep_deg=0.25)
            hlog('  cand%d MoveJ_Test(0.25)=%s' % (idx, st))
            if st == 0:
                found = end
                break
        hlog('found=%s' % ([round(v, 2) for v in found] if found else None))
        if found:
            prog = RDK.AddProgram('_repro_struct_复核', robot)
            try:
                prog.setVisible(False)
                prog.setPoseFrame(robot.PoseFrame())
                prog.setPoseTool(robot.PoseTool())
                prog.MoveJ(start)
                prog.MoveJ(found)
                msg, matrix, status = prog.InstructionListJoints(mm_step=1, deg_step=1, collision_check=COLLISION_ON)
                hlog('整段复核 status=%s msg=%r' % (status, (msg or '')[:100]))
            finally:
                prog.Delete()
    RDK.Render(True)
    RDK.setRunMode(RUNMODE_RUN_ROBOT)
    hlog('run_precheck 完成（进程存活）')

def full_work():
    try:
        stop_ev = threading.Event()
        ka = None
        if MODE != 'nokeepalive':
            ka = threading.Thread(target=driver_keepalive, args=(stop_ev, 'work'), daemon=True)
            ka.start()
            hlog('保活线程已启动')
        if MODE != 'nosock':
            q = read_feedback_once()
            hlog('30004 读一帧=%s' % (['%.2f' % v for v in q] if q else None))
        run_precheck()
        stop_ev.set()
        if MODE != 'notk':
            root.destroy()
    except BaseException as e:
        import traceback
        hlog('FATAL in full_work: %s' % traceback.format_exc())
        try:
            root.destroy()
        except Exception:
            pass

if MODE == 'notk':
    full_work()
    hlog('===== notk 模式结束，进程存活 =====')
    sys.exit(0)

root = tk.Tk()
root.title('结构复现 ' + MODE)
root.geometry('360x120')
tk.Label(root, text='结构复现运行中: ' + MODE).pack(padx=10, pady=10)
tlog = tk.Text(root, height=3)
tlog.pack(padx=10, pady=4)
root.after(1500, full_work)
try:
    root.mainloop()
except BaseException:
    import traceback
    hlog('FATAL mainloop: ' + traceback.format_exc())
    raise
hlog('===== struct repro 正常结束，进程存活 =====')
