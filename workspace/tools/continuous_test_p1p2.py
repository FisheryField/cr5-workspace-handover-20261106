#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""连续运动测试：原点 -> P1 -> P2（只做这三条，绝不多写）。

P1 / P2 的关节值 = 2026-09-27 你那两次【单步运动】在控制器日志里的原文：
    10:56:45  recv = JointMovJ(16.379607,-6.735621,-111.802214,28.537835,90.000000,-73.620393)   <- P1
    11:01:22  recv = JointMovJ(-77.933681,-57.346998,-65.452613,122.799611,77.933681,-0.000000)  <- P2

与两次单步的唯一区别（就是本次要测的东西）：
    · 单步：发一条 -> 等它走完 -> 再发下一条                     （点间会停住）
    · 本脚本：三条【连续下发、之间不等待完成】，最后只 Sync() 一次  （点间不停）

除下面那三个 JointMovJ 和一次 Sync() 之外，不发送任何其它指令：
    不 EnableRobot / 不 DisableRobot / 不 SpeedFactor / 不 SetCollide / 不 ClearError / 不改任何配置。

端口说明（实测）：命令口【同一时刻只服务一个客户端】——
    30003 的 accept 队列已积压（Recv-Q=2，不再 accept），29999 正被 RoboDK 占着。
    所以本脚本要在【RoboDK 断开连接】之后才能用。
    若不想断 RoboDK：改用最小轨迹 JSON `测试_原点P1P2.json`，走 RoboDK 自己的通道（推荐）。

用法:
    python tools/continuous_test_p1p2.py            # dry-run：只打印（不连控制器）
    python tools/continuous_test_p1p2.py --check    # 只读自检：连上后读 RobotMode/GetAngle（不发运动）
    python tools/continuous_test_p1p2.py --go       # 真正发送三条 + Sync()
"""
import socket
import sys
import time

# 控制台编码兜底：否则在非 UTF-8 控制台上 print 中文会抛 UnicodeEncodeError（表现为"运行不了"）
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

HOST = '192.168.5.1'
PORT = 29999   # ★ RoboDK 走的就是这个口；30003 已因积压连接而不再 accept

# ★ 原样照抄日志，一位不改。
COMMANDS = [
    'JointMovJ(0.000000,0.000000,0.000000,0.000000,0.000000,0.000000)',            # 原点
    'JointMovJ(16.379607,-6.735621,-111.802214,28.537835,90.000000,-73.620393)',   # P1（日志 10:56:45）
    'JointMovJ(-77.933681,-57.346998,-65.452613,122.799611,77.933681,-0.000000)',  # P2（日志 11:01:22）
]
SYNC = 'Sync()'


def send(s, cmd, wait=0.6):
    s.sendall((cmd + '\n').encode())
    time.sleep(wait)
    try:
        return s.recv(4096).decode('utf-8', 'replace').strip().replace('\n', ' ')
    except socket.timeout:
        return '(no reply)'
    except ConnectionResetError:
        return '(连接被控制器重置 —— 该口已被别的客户端占用)'


def connect():
    try:
        s = socket.create_connection((HOST, PORT), timeout=8)
        s.settimeout(6)
        return s
    except Exception as e:  # noqa: BLE001
        print('')
        print('!! 连不上控制器命令口 %s:%d —— %s: %s' % (HOST, PORT, type(e).__name__, e))
        print('   已知原因：命令口同一时刻只服务一个客户端。')
        print('     · 29999 被 RoboDK 占着 -> 先在 RoboDK 里断开连接，或直接退出 RoboDK')
        print('     · 30003 的 accept 队列已积压 -> 不要再用 30003')
        print('   推荐替代：把 `测试_原点P1P2.json` 交给 RoboDK 脚本以"连续运动"执行。')
        return None


def show_plan():
    print('目标: %s:%d' % (HOST, PORT))
    print('将按顺序【连续下发】以下 %d 条，然后 Sync() 一次：' % len(COMMANDS))
    for i, c in enumerate(COMMANDS, 1):
        tag = '原点' if i == 1 else 'P%d' % (i - 1)
        print('   %d) [%s] %s' % (i, tag, c))
    print('   %d) [同步] %s' % (len(COMMANDS) + 1, SYNC))


def main():
    go = '--go' in sys.argv
    check = '--check' in sys.argv
    show_plan()

    if check:
        print('')
        print('--- 只读自检（不发送任何运动指令）---')
        s = connect()
        if s is None:
            return 2
        for c in ('RobotMode()', 'GetAngle()', 'GetErrorID()'):
            print('   %-13s -> %s' % (c, send(s, c)))
        s.close()
        print('   连接正常 ✓（要真正运动请加 --go）')
        return 0

    if not go:
        print('')
        print('(dry-run：未发送任何指令。要真正执行请加 --go；想先验证连通性用 --check)')
        return 0

    s = connect()
    if s is None:
        return 2
    print('')
    t0 = time.time()
    for i, c in enumerate(COMMANDS, 1):
        t = time.time() - t0
        r = send(s, c)
        print('  +%5.2fs  发送 %s' % (t, c))
        print('            -> %s' % r)
    t = time.time() - t0
    print('  +%5.2fs  发送 %s' % (t, SYNC))
    r = send(s, SYNC, wait=1.0)
    print('            -> %s' % r)
    print('  +%5.2fs  结束（总耗时 %.2fs）' % (time.time() - t0, time.time() - t0))
    s.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
