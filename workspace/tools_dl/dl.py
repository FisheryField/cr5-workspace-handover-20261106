#!/usr/bin/env python3
"""Tiny downloader: tries direct, then the local HTTP proxy, and reports TLS details."""
import ssl, socket, sys, urllib.request, urllib.error, os, time

PROXY = ('127.0.0.1', 7897)

def tls_probe(host='github.com', use_proxy=True):
    s = socket.create_connection(PROXY if use_proxy else (host, 443), timeout=15)
    if use_proxy:
        s.sendall(('CONNECT %s:443 HTTP/1.1\r\nHost: %s:443\r\n\r\n' % (host, host)).encode())
        buf = b''
        while b'\r\n\r\n' not in buf:
            c = s.recv(1)
            if not c:
                raise RuntimeError('proxy closed during CONNECT')
            buf += c
        line = buf.split(b'\r\n')[0].decode('latin1')
        if '200' not in line:
            raise RuntimeError('proxy refused: ' + line)
    ctx = ssl.create_default_context()
    ss = ctx.wrap_socket(s, server_hostname=host)
    ss.sendall(('HEAD / HTTP/1.0\r\nHost: %s\r\nConnection: close\r\n\r\n' % host).encode())
    data = ss.recv(64)
    return ss.version(), data.split(b'\r\n')[0].decode('latin1', 'replace')

def download(url, out, use_proxy=True, chunk=1 << 20):
    handlers = []
    if use_proxy:
        handlers.append(urllib.request.ProxyHandler({
            'http': 'http://%s:%d' % PROXY, 'https': 'http://%s:%d' % PROXY}))
    opener = urllib.request.build_opener(*handlers)
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    t0 = time.time()
    with opener.open(req, timeout=60) as r, open(out, 'wb') as f:
        total = int(r.headers.get('Content-Length') or 0)
        done = 0
        while True:
            b = r.read(chunk)
            if not b:
                break
            f.write(b)
            done += len(b)
            if total and done % (16 * chunk) < chunk:
                print('  %.1f%% %d/%d  %.1f MB/s' % (100.0 * done / total, done, total,
                                                     done / 1048576.0 / max(time.time() - t0, 1e-6)), flush=True)
    return done

if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'probe':
        for mode in (True, False):
            try:
                print('proxy=%s -> %s' % (mode, tls_probe(use_proxy=mode)))
            except Exception as e:
                print('proxy=%s -> FAIL %s: %s' % (mode, type(e).__name__, e))
    elif cmd == 'get':
        url, out = sys.argv[2], sys.argv[3]
        for mode in (True, False):
            try:
                n = download(url, out, use_proxy=mode)
                print('OK %d bytes via proxy=%s' % (n, mode))
                break
            except Exception as e:
                print('FAIL proxy=%s: %s: %s' % (mode, type(e).__name__, e))
