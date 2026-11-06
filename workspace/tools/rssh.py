#!/usr/bin/env python3
"""rssh.py — 控制箱 SSH 只读执行器（paramiko 版，替代损坏的 ssh.exe 通路）。

用法:
  python tools/rssh.py "cat /tmp/codesysBoot"
  python tools/rssh.py -f script.sh        # 在控制箱上执行本地脚本 (sh -s)
  python tools/rssh.py --put local remote  # 上传
  python tools/rssh.py --get remote local  # 下载

凭据沿用工作区约定: root / dobot @ 192.168.5.1。
只做执行/传文件，不做任何交互式编辑。
"""
import sys, os

# ★ 输出统一走 UTF-8（否则远端回来的中文/符号在 GBK 控制台上会抛
#   UnicodeEncodeError: 'gbk' codec can't encode character ... ，把整条命令的
#   输出吞掉、看起来像命令失败）。必须在任何 print 之前设置。
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001  老版本 Python 没有 reconfigure
    pass

HOST = "192.168.5.1"
USER = "root"
PASS = "dobot"


def main():
    import paramiko
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cli.connect(HOST, username=USER, password=PASS, timeout=15,
                allow_agent=False, look_for_keys=False)
    try:
        if args[0] == "-f":
            with open(args[1], "r", encoding="utf-8", newline="\n") as f:
                script = f.read()
            if not script.endswith("\n"):
                script += "\n"
            stdin, stdout, stderr = cli.exec_command("sh -s", timeout=120)
            stdin.write(script)
            stdin.channel.shutdown_write()
            out = stdout.read().decode("utf-8", "replace")
            err = stderr.read().decode("utf-8", "replace")
            rc = stdout.channel.recv_exit_status()
            sys.stdout.write(out)
            if err:
                sys.stdout.write("--- stderr ---\n" + err)
            return rc
        if args[0] == "--put":
            sftp = cli.open_sftp()
            sftp.put(args[1], args[2])
            sftp.close()
            print("put %s -> %s" % (args[1], args[2]))
            return 0
        if args[0] == "--get":
            sftp = cli.open_sftp()
            sftp.get(args[1], args[2])
            sftp.close()
            print("get %s -> %s" % (args[1], args[2]))
            return 0
        cmd = " ".join(args)
        stdin, stdout, stderr = cli.exec_command(cmd, timeout=120)
        out = stdout.read().decode("utf-8", "replace")
        err = stderr.read().decode("utf-8", "replace")
        rc = stdout.channel.recv_exit_status()
        sys.stdout.write(out)
        if err:
            sys.stdout.write("--- stderr ---\n" + err)
        return rc
    finally:
        cli.close()


if __name__ == "__main__":
    sys.exit(main())
