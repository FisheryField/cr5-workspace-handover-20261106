"""RoboDK station macro that uploads the reviewed P1 project on button click."""
import errno
import hashlib
from pathlib import Path
import re
import socket
import sys
import threading
import tkinter as tk
from tkinter import ttk
import uuid

WORKSPACE = Path(r"D:\mydata\glm-workplace")
PROJECT_NAME = "CR5_Traj17_Full28_RoboDKPace"
PROJECT = WORKSPACE / "sim_scripts/rdk_station_dump/cr5_controller_deployment_check" / PROJECT_NAME
REMOTE_ROOT = "/dobot/userdata/project/project"
FILES = ("prj.json", "global.lua", "point.json", "point.json.lua", "src0.lua")
EXPECTED = {'global.lua': '01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b', 'point.json': '37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570', 'point.json.lua': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', 'prj.json': '14f1471434bc39ae6f11944fdff35eff23d14d9e65682650c694a0375f86ce9c', 'src0.lua': '5889e022a43365d78f85ab650097dabf7ff66018b7a2c0044cdb4f4f95aacb05'}
IK_CHECKS = [(3, 'InverseSolution(0.003754307,-421.107332356,419.982417296,-90.002245214,0.001098771,-179.999001411,0,0,1,{58.476472373,-0.960852162,140.333450443,-139.002031791,-57.804694642,-0.423423212})', [64.02228797203567, 6.448332743488223, 132.2473338835222, -138.39422819170474, -63.354552917896406, -0.3241682485250235]), (4, 'InverseSolution(119.995763127,-421.166424470,419.898211807,-90.016467328,0.001025702,-179.999999859,0,0,1,{64.021287972,6.446332743,132.246833884,-138.394228192,-63.354552918,-0.324168249})', [86.57747720905265, 9.28927322245804, 128.7082510257699, -137.79480132658523, -85.91633228186147, -0.20684764089688623]), (6, 'InverseSolution(20.012787207,-421.112577775,420.018584802,89.997223800,0.001138351,0.001001881,0,0,1,{86.577477209,9.276273222,128.708251026,-137.798301327,-85.916332282,179.793152359})', [67.69090885775437, 6.529675848700542, 132.14241617535345, -138.3985466934893, -67.02333541726536, 179.69675137221736]), (7, 'InverseSolution(-134.997864228,-421.176903392,419.988392357,90.001025841,-0.001093998,0.000999818,0,0,1,{67.689908858,6.532675849,132.142416175,-138.398546693,-67.023335417,179.696751372})', [43.20055450927402, 9.992436931745914, 127.7775354986438, -137.30780561848053, -42.53972603938887, 179.5328027540226]), (10, 'InverseSolution(0.009571781,-538.794246390,550.033286006,179.996140455,-0.001050991,0.001499448,0,0,1,{-73.903815418,-4.387986350,-72.292007184,-13.492006285,89.708975608,195.817662999})', [-74.60332217170071, -7.635972994984292, -68.63085952054624, -13.901195998906598, 89.73433319456183, 195.1213113383559]), (11, 'InverseSolution(-124.990770022,-538.674548629,550.290868316,179.967015712,-0.001015181,0.001499351,0,0,1,{-74.604822172,-7.638472995,-68.632359521,-13.901195999,89.734333195,195.121311338})', [-88.07802526144006, -9.705765074624768, -66.149680498234, -14.283600355601104, 89.75069206514154, 181.6509545702485]), (13, 'InverseSolution(0.001913743,-538.783175632,550.034745513,-179.996143365,0.001062126,-179.999002229,0,0,1,{-88.079525261,-9.726765075,-66.161680498,-14.283600356,89.750692065,1.650954570})', [-74.60381123099108, -7.63441932644509, -68.632421850568, -13.90118723112358, 89.7343328532127, 15.121322324694681]), (14, 'InverseSolution(124.996421201,-538.788895033,550.021815524,-179.997793329,0.001175622,-179.999501574,0,0,1,{-74.604811231,-7.638419326,-68.632421851,-13.901187231,89.734332853,15.121322325})', [-61.956465055286216, -9.722890875776704, -66.1633371160166, -14.283317761193452, 89.75068128958331, 27.773511712762613]), (16, 'InverseSolution(-100.005434305,-538.807206099,419.981073079,89.998868151,-0.001652008,90.000004542,0,0,1,{54.026856247,22.645931211,68.332129331,89.289070327,-36.384114747,-0.204476142})', [55.29841389637225, 28.25288663730979, 59.82726865413243, 92.25280093331367, -35.07853222105949, -0.2829254366772495]), (18, 'InverseSolution(-99.996030126,-538.816996684,419.981072784,55.584047548,89.997997448,55.585052074,0,0,1,{54.027374103,22.647055699,68.330482945,89.289606163,-36.383590760,-90.204493618})', [55.29988053891107, 28.254093448819244, 59.8253738545653, 92.25350482341338, -35.078057508382656, -90.28294462922608]), (20, 'InverseSolution(-100.005434203,-538.820191403,419.981072603,-55.584337226,-89.997997448,-124.415658247,0,0,1,{54.027692077,22.647746181,68.329471983,89.289935201,-36.383269020,-270.204504349})', [55.29916706766452, 28.25483448547776, 59.82421034880211, 92.25393705722911, -35.0777660240456, -270.2829564143973]), (22, 'InverseSolution(-89.994235147,-538.768415790,418.774693036,-88.932013497,-59.662992591,-90.935983131,0,0,1,{54.921360711,22.389719249,69.062968965,89.746877148,-35.480462216,-240.632770892})', [56.146377318180754, 27.978671384308612, 60.6108901033771, 92.70520977563254, -34.22260813285, -240.74865933374753]), (23, 'InverseSolution(-89.994135500,-498.768458949,418.774570556,-88.932026871,-59.662985211,-90.935966679,0,0,1,{56.146377318,27.978671384,60.610890103,92.705209776,-34.222608133,-240.748659334})', [53.698437496976645, 22.210723088523856, 69.3237275039943, 89.62918086185952, -36.70425153612599, -240.5877998285749]), (26, 'InverseSolution(-89.925910957,-535.067652315,418.774693063,-88.932013051,59.663007479,-90.936006236,0,0,1,{53.575924462,21.931482163,69.729656174,89.548412826,-34.984751586,-121.310541581})', [55.75062496390132, 26.937697766183874, 62.22998607697541, 92.16659429522065, -32.78156214675861, -121.46086253606838]), (27, 'InverseSolution(-89.925815024,-495.067696727,418.774573475,-88.932026043,59.663014753,-90.936012931,0,0,1,{55.750624964,26.937697766,62.229986077,92.166594295,-32.781562147,-121.460862536})', [53.24315316587918, 21.24010095670836, 70.7277564145414, 89.22486049132665, -35.32102338643413, -121.28979375212619])]


def exists(sftp, path):
    try:
        sftp.stat(path)
    except OSError as error:
        if error.errno == errno.ENOENT:
            return False
        raise
    return True


def upload(allow_create=True):
    sys.path.insert(0, str(WORKSPACE / "tools"))
    import rssh
    import paramiko

    content = {name: (PROJECT / name).read_bytes() for name in FILES}
    if {name: hashlib.sha256(data).hexdigest() for name, data in content.items()} != EXPECTED:
        raise RuntimeError("本地工程与已核对版本不一致。")
    target = REMOTE_ROOT + "/" + PROJECT_NAME
    pending = REMOTE_ROOT + "/." + PROJECT_NAME + "_" + uuid.uuid4().hex
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(rssh.HOST, username=rssh.USER, password=rssh.PASS,
                       timeout=8, allow_agent=False, look_for_keys=False)
        with client.open_sftp() as sftp:
            sftp.get_channel().settimeout(8)

            def verify(folder):
                for name, data in content.items():
                    with sftp.open(folder + "/" + name, "rb") as file:
                        if file.read() != data:
                            raise RuntimeError("回读不一致：" + name)

            if exists(sftp, target):
                verify(target)
                return "工程已在控制器，文件回读一致。"
            if not allow_create:
                raise RuntimeError("请先上传工程。")
            sftp.mkdir(pending)
            try:
                for name, data in content.items():
                    with sftp.open(pending + "/" + name, "wb") as file:
                        file.write(data)
                verify(pending)
                sftp.rename(pending, target)
            except Exception:
                if exists(sftp, pending):
                    for name in FILES:
                        path = pending + "/" + name
                        if exists(sftp, path):
                            sftp.remove(path)
                    sftp.rmdir(pending)
                raise
            verify(target)
            return "上传完成，控制器端 5 个文件回读一致。"
    finally:
        client.close()


dashboard_lock = threading.Lock()
stop_requested = threading.Event()


def stop_project():
    sys.path.insert(0, str(WORKSPACE / "tools"))
    import rssh
    with dashboard_lock, socket.create_connection((rssh.HOST, 29999), timeout=3) as connection:
        connection.sendall(b"StopScript()")
        data = b""
        try:
            while b";" not in data:
                chunk = connection.recv(4096)
                if not chunk:
                    break
                data += chunk
        except OSError:
            pass
    reply = data.decode("ascii", errors="replace")
    if not reply:
        raise RuntimeError("软停未收到应答，无法确认停止。")
    if not re.fullmatch(r"\s*0,\{\},StopScript\(\);\s*", reply):
        raise RuntimeError("软停未获确认：" + reply)
    return "控制器已接受软停。请确认机械臂已停稳。"


def start_project():
    upload(allow_create=False)
    import rssh

    def command(connection, request):
        connection.sendall(request.encode("ascii"))
        data = b""
        while b";" not in data:
            chunk = connection.recv(4096)
            if not chunk:
                raise RuntimeError("命令口无应答，请确认 RoboDK 驱动已断开。")
            data += chunk
        return data.decode("ascii", errors="replace")

    def values(reply):
        match = re.match(r"^\s*0,\{([^}]*)\}", reply)
        if not match:
            raise RuntimeError("控制器拒绝查询：" + reply)
        return [float(value) for value in match.group(1).split(",") if value]

    with dashboard_lock, socket.create_connection((rssh.HOST, 29999), timeout=4) as connection:
        if values(command(connection, "RobotMode()")) != [5.0]:
            raise RuntimeError("控制器未处于已使能待机状态。")
        axes = values(command(connection, "GetAngle()"))
        if len(axes) != 6 or not all(abs(angle) <= 0.05 for angle in axes):
            raise RuntimeError("六轴起始角度不在零位容差内。")
        for point, request, expected in IK_CHECKS:
            if stop_requested.is_set():
                return "已取消本次启动。"
            try:
                joints = values(command(connection, request))
            except Exception as error:
                raise RuntimeError(f"P{point} 控制器逆解查询失败：{error}") from error
            if len(joints) != 6 or any(abs(a-b) > 0.005 for a,b in zip(joints, expected)):
                raise RuntimeError(f"P{point} 控制器逆解与预检分支不一致。")
        if stop_requested.is_set():
            return "已取消本次启动。"
        connection.sendall(("RunScript(" + PROJECT_NAME + ")").encode("ascii"))
        try:
            reply = connection.recv(4096).decode("ascii", errors="replace")
        except OSError:
            return "启动命令已发送，应答未确认。请查看控制器状态，避免重复点击。"
        if not reply:
            return "启动命令已发送，应答未确认。请查看控制器状态，避免重复点击。"
        if not re.match(r"^\s*0,", reply):
            raise RuntimeError("控制器拒绝启动：" + reply)
    return "控制器已接受启动命令。实机将从零位执行轨迹17，逐段检查。"


def request_stop():
    stop_requested.set()
    stop_button.configure(state="disabled")
    stop_status.set("正在请求控制器停止…")

    def worker():
        try:
            message = stop_project()
        except Exception as error:
            message = "软停未确认：" + str(error)
        window.after(0, stop_finished, message)

    threading.Thread(target=worker, daemon=False).start()


def stop_finished(message):
    stop_status.set(message)
    stop_button.configure(state="normal")


def run_action(action, pending, lock_start=False):
    if lock_start:
        stop_requested.clear()
        stop_status.set("")
    button.configure(state="disabled")
    start_button.configure(state="disabled")
    status.set(pending)

    def worker():
        try:
            message = action()
            locked = lock_start
        except Exception as error:
            message = "操作未完成：" + str(error)
            locked = False
        try:
            window.after(0, finish, message, locked)
        except (RuntimeError, tk.TclError):
            pass

    threading.Thread(target=worker, daemon=False).start()


def finish(message, locked):
    status.set(message)
    button.configure(state="normal")
    if not locked:
        start_button.configure(state="normal")


if __name__ == "__main__":
    window = tk.Tk()
    window.title("CR5 轨迹17（RoboDK节奏28点） 工程上传")
    status = tk.StringVar(value="等待上传。上传与启动分开。点击启动后，实机从零位执行RoboDK节奏28点，任一检查失败即停止。")
    ttk.Label(window, text=PROJECT_NAME, padding=12).pack()
    button = ttk.Button(window, text="上传到控制器", command=lambda: run_action(upload, "正在上传并校验…"))
    button.pack(pady=5)
    start_button = ttk.Button(window, text="启动轨迹17（RoboDK节奏28点）（实机运动）",
                              command=lambda: run_action(start_project, "核对工程及控制器状态…", True))
    start_button.pack(pady=5)
    stop_button = tk.Button(window, text="软停（结束当前程序）", fg="white", bg="#9b2626", command=request_stop)
    stop_button.pack(pady=8)
    stop_status = tk.StringVar(value="")
    ttk.Label(window, textvariable=stop_status, wraplength=480).pack()
    ttk.Label(window, textvariable=status, wraplength=480, padding=12).pack()
    window.mainloop()
