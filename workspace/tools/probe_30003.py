# -*- coding: utf-8 -*-
"""只读探测：30003 是命令口还是反馈口？只发只读命令 RobotMode()/GetAngle()。"""
import socket
import sys
import time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HOST = "192.168.5.1"

s = socket.create_connection((HOST, 30003), timeout=6)
s.settimeout(3)
print("connected to 30003")
time.sleep(0.5)
try:
    d = s.recv(4096)
    print("被动接收 %d 字节: %r" % (len(d), d[:60]))
    feedback = True
except socket.timeout:
    print("被动接收：超时（没有主动推送）→ 可能是命令口")
    feedback = False

for cmd in ["RobotMode()", "GetAngle()"]:
    try:
        s.sendall((cmd + "\n").encode())
    except Exception as exc:
        print("%s 发送失败 %s: %s" % (cmd, type(exc).__name__, exc))
        break
    time.sleep(0.8)
    try:
        d = s.recv(4096)
        print("%s -> %r" % (cmd, d.decode('utf-8', 'replace').strip()[:200]))
    except socket.timeout:
        print("%s -> 超时无应答" % cmd)
    except Exception as exc:
        print("%s -> 接收异常 %s: %s" % (cmd, type(exc).__name__, exc))
        break
s.close()
print("feedback_port_guess =", feedback)
