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
PROJECT_NAME = "CR5_Traj17_Full27_RoboDKPace"
PROJECT = WORKSPACE / "sim_scripts/rdk_station_dump/cr5_controller_deployment_check" / PROJECT_NAME
REMOTE_ROOT = "/dobot/userdata/project/project"
FILES = ("prj.json", "global.lua", "point.json", "point.json.lua", "src0.lua")
EXPECTED = {'global.lua': '01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b', 'point.json': '37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570', 'point.json.lua': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', 'prj.json': '14f1471434bc39ae6f11944fdff35eff23d14d9e65682650c694a0375f86ce9c', 'src0.lua': '377a4d50c6be66a7f172615620e3c2dfbea6974c79de756984039c388a01cd41'}


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
    window.title("CR5 轨迹17（RoboDK节奏27点） 工程上传")
    status = tk.StringVar(value="等待上传。上传与启动分开。点击启动后，实机从零位执行RoboDK节奏27点，任一检查失败即停止。")
    ttk.Label(window, text=PROJECT_NAME, padding=12).pack()
    button = ttk.Button(window, text="上传到控制器", command=lambda: run_action(upload, "正在上传并校验…"))
    button.pack(pady=5)
    start_button = ttk.Button(window, text="启动轨迹17（RoboDK节奏27点）（实机运动）",
                              command=lambda: run_action(start_project, "核对工程及控制器状态…", True))
    start_button.pack(pady=5)
    stop_button = tk.Button(window, text="软停（结束当前程序）", fg="white", bg="#9b2626", command=request_stop)
    stop_button.pack(pady=8)
    stop_status = tk.StringVar(value="")
    ttk.Label(window, textvariable=stop_status, wraplength=480).pack()
    ttk.Label(window, textvariable=status, wraplength=480, padding=12).pack()
    window.mainloop()
