# -*- coding: utf-8 -*-
"""确认 29999 到底该用什么语法；并对比 30003/30005/30006 的角色（全部只读）。"""
import socket, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
CTRL = '192.168.5.1'

def probe(port, cmds, wait=4.0, first_wait=2.0):
    print('\n===== %d =====' % port)
    try:
        s = socket.create_connection((CTRL, port), timeout=5.0); s.settimeout(wait)
    except Exception as e:
        print('  连不上:', e); return
    try:
        b0 = b''
        t0 = time.time()
        while time.time() - t0 < first_wait:
            try:
                p = s.recv(4096)
            except socket.timeout:
                break
            if not p: break
            b0 += p
            if len(b0) > 200: break
        print('  首包(%d B): %r' % (len(b0), b0[:120]))
        for c in cmds:
            s.sendall((c + '\n').encode())
            b = b''
            t1 = time.time()
            while time.time() - t1 < wait:
                try:
                    p = s.recv(4096)
                except socket.timeout:
                    break
                if not p: break
                b += p
                if b'}' in b or b';\n' in b: break
            print('  %-22s → %r' % (c, b.decode('utf-8', 'replace').strip()[:150]))
    finally:
        s.close()

probe(29999, ['EnableRobot()', 'GetPose()', 'RobotMode();', 'ClearError()'])
probe(30005, ['GetAngle()', 'RobotMode()'])
probe(30006, ['GetAngle()'])
