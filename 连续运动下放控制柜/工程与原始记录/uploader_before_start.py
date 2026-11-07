"""RoboDK station macro that uploads the reviewed P1 project on button click."""
import errno
import hashlib
from pathlib import Path
import sys
import threading
import tkinter as tk
from tkinter import ttk
import uuid

WORKSPACE = Path(r"D:\mydata\glm-workplace")
PROJECT_NAME = "CR5_Traj17_ZeroToP1"
PROJECT = WORKSPACE / "sim_scripts/rdk_station_dump/cr5_controller_deployment_check" / PROJECT_NAME
REMOTE_ROOT = "/dobot/userdata/project/project"
FILES = ("prj.json", "global.lua", "point.json", "point.json.lua", "src0.lua")
EXPECTED = {'global.lua': '01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b', 'point.json': '37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570', 'point.json.lua': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', 'prj.json': '14f1471434bc39ae6f11944fdff35eff23d14d9e65682650c694a0375f86ce9c', 'src0.lua': 'c66c50b254430aadf534d1c7742c74fdf04aac4593f4b490c3d254d51c0740ae'}


def exists(sftp, path):
    try:
        sftp.stat(path)
    except OSError as error:
        if error.errno == errno.ENOENT:
            return False
        raise
    return True


def upload():
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


def on_click():
    button.configure(state="disabled")
    status.set("正在上传并校验…")

    def worker():
        try:
            message = upload()
        except Exception as error:
            message = "上传未完成：" + str(error)
        try:
            window.after(0, finish, message)
        except (RuntimeError, tk.TclError):
            pass

    threading.Thread(target=worker, daemon=False).start()


def finish(message):
    status.set(message)
    button.configure(state="normal")


if __name__ == "__main__":
    window = tk.Tk()
    window.title("CR5 零位→P1 工程上传")
    status = tk.StringVar(value="等待上传。工程包含一条低速 MoveJ，启动需在控制器端操作。")
    ttk.Label(window, text=PROJECT_NAME, padding=12).pack()
    button = ttk.Button(window, text="上传到控制器", command=on_click)
    button.pack(pady=5)
    ttk.Label(window, textvariable=status, wraplength=480, padding=12).pack()
    window.mainloop()
