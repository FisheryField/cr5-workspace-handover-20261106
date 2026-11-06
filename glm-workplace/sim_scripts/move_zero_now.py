# -*- coding: utf-8 -*-
"""实机归零：MoveJ → [0,0,0,0,0,0]，带假断连容忍；30004 轮询到位判据。
用户明确要求归零；发送前打印起点；全程监控。
"""
import sys, io, time, socket, struct, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
from robodk.robolink import *

def fb():
    with socket.create_connection(('192.168.5.1', 30004), timeout=3.0) as conn:
        packet = bytearray()
        while len(packet) < 1440:
            part = conn.recv(1440 - len(packet))
            if not part:
                raise RuntimeError('反馈连接关闭')
            packet.extend(part)
    q = list(struct.unpack_from('<6d', packet, 192))
    vel = list(struct.unpack_from('<6d', packet, 480))
    mode = struct.unpack_from('<Q', packet, 24)[0]
    return q, vel, mode

RDK = Robolink()
robot = RDK.Item('', ITEM_TYPE_ROBOT)
RDK.setRunMode(RUNMODE_RUN_ROBOT)

q0, v0, m0 = fb()
print('起点: mode=%d 关节=[%s]' % (m0, ', '.join('%.2f' % v for v in q0)))
if max(abs(v) for v in q0) < 0.05:
    print('已经在零位，无需运动。')
    sys.exit(0)

print('发送 MoveJ → 零位…')
sent_ok = False
for attempt in range(3):
    try:
        robot.Connect()
        robot.MoveJ([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        sent_ok = True
        print('MoveJ 调用返回（按驱动习性可能伴随假断连报错，以反馈为准）。')
        break
    except StoppedError as exc:
        print('第%d次发送伴随: %s —— 轮询反馈判断是否在动…' % (attempt + 1, exc))
        # 假断连：指令可能已上线，轮询 15s 看是否起步
        t0 = time.time(); started = False
        while time.time() - t0 < 15.0:
            try:
                q, vel, mode = fb()
                if max(abs(a - b) for a, b in zip(q, q0)) > 1.0:
                    started = True
                    break
            except Exception:
                pass
            time.sleep(0.5)
        if started:
            print('反馈显示已起步 → 继续等待到位。')
            sent_ok = True
            break
        print('15s 无位移，重连后重试发送。')
    except Exception as exc:
        print('发送异常: %r —— 2s 后重试' % exc)
        time.sleep(2)

if not sent_ok:
    print('!!! 三次发送均未能确认上线，停止。请用示教器归零。')
    sys.exit(1)

# 到位轮询：|q|<0.5 且静止
t0 = time.time()
last = None
while time.time() - t0 < 120.0:
    try:
        q, vel, mode = fb()
    except Exception as e:
        print('反馈读取: %s' % e)
        time.sleep(0.5)
        continue
    err = max(abs(v) for v in q)
    cur = tuple(round(v, 1) for v in q)
    if cur != last:
        print('[%5.1fs] mode=%d 关节=[%s] err_max=%.2f' % (time.time() - t0, mode, ', '.join('%.2f' % v for v in q), err))
        last = cur
    if err < 0.5 and max(abs(v) for v in vel) < 1.0:
        print('✅ 已归零（|q|max=%.3f，mode=%d）。' % (err, mode))
        sys.exit(0)
    time.sleep(1.0)

q, vel, mode = fb()
print('⚠️ 120s 未到零位，当前位置=[%s] mode=%d —— 停止等待，待判读。' % (', '.join('%.2f' % v for v in q), mode))
sys.exit(2)
