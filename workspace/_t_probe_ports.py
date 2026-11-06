# -*- coding: utf-8 -*-
"""只读探测 29999 与 30003：看哪个端口能作为独立命令通道（只发只读命令）。"""
import socket, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
CTRL = '192.168.5.1'

def probe(port, cmds, wait=6.0):
    print('\n===== %s:%d =====' % (CTRL, port))
    try:
        s = socket.create_connection((CTRL, port), timeout=5.0); s.settimeout(wait)
    except Exception as e:
        print('  连接失败:', e); return
    try:
        buf = b''
        t0 = time.time()
        while time.time() - t0 < 2.0:
            try:
                c = s.recv(4096)
            except socket.timeout:
                break
            if not c: break
            buf += c
            if b'{}' in buf: break
        print('  开连后首包: %r' % buf[:160])
        for c in cmds:
            s.sendall((c + '\n').encode())
            b = b''
            t1 = time.time()
            while time.time() - t1 < wait:
                try:
                    part = s.recv(4096)
                except socket.timeout:
                    break
                if not part: break
                b += part
                if b'}' in b: break
            print('  %-16s → %r' % (c, b.decode('utf-8', 'replace').strip()[:140]))
    finally:
        s.close()

probe(29999, ['RobotMode()', 'GetAngle()', 'GetErrorID()'])
probe(30003, ['RobotMode()', 'GetAngle()'])
