#!/usr/bin/env python3
"""Trace the GitHub release-asset redirect and try a ranged GET on the final URL."""
import ssl, socket, sys

URL = 'https://github.com/TEdit/Terraria-Map-Editor/releases/download/5.2.5/TEdit-stable-Portable.zip'


def connect(host, port=443, proxy=None):
    s = socket.create_connection(proxy or (host, port), timeout=20)
    if proxy:
        s.sendall(('CONNECT %s:%d HTTP/1.1\r\nHost: %s:%d\r\n\r\n' % (host, port, host, port)).encode())
        buf = b''
        while b'\r\n\r\n' not in buf:
            c = s.recv(1)
            if not c:
                raise RuntimeError('proxy closed during CONNECT')
            buf += c
        if b'200' not in buf.split(b'\r\n')[0]:
            raise RuntimeError('proxy refused: ' + buf.split(b'\r\n')[0].decode('latin1'))
    ctx = ssl.create_default_context()
    return ctx.wrap_socket(s, server_hostname=host)


def head(url, proxy=None):
    host, _, path = url.split('/', 3)[2], '', url.split('/', 3)[3]
    path = '/' + path
    s = connect(host, proxy=proxy)
    req = 'GET %s HTTP/1.1\r\nHost: %s\r\nUser-Agent: Mozilla/5.0\r\nRange: bytes=0-1023\r\nConnection: close\r\n\r\n' % (path, host)
    s.sendall(req.encode())
    data = b''
    while len(data) < 8192:
        chunk = s.recv(4096)
        if not chunk:
            break
        data += chunk
        if b'\r\n\r\n' in data and len(data) > 2000:
            break
    head_txt = data.split(b'\r\n\r\n')[0].decode('latin1')
    s.close()
    return head_txt


if __name__ == '__main__':
    for proxy in (None, ('127.0.0.1', 7897)):
        try:
            h = head(URL, proxy)
            print('=== proxy=%s ===' % (proxy,))
            print('\n'.join(h.split('\r\n')[:6]))
            loc = [l for l in h.split('\r\n') if l.lower().startswith('location:')]
            print('LOCATION:', loc[0] if loc else '(none)')
            if loc:
                final = loc[0].split(':', 1)[1].strip()
                h2 = head(final, proxy)
                print('--- final host ---')
                print('\n'.join(h2.split('\r\n')[:6]))
        except Exception as e:
            print('=== proxy=%s === FAIL %s: %s' % (proxy, type(e).__name__, e))
