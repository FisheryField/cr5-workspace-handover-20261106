#!/usr/bin/env python3
"""Robust direct download for GitHub release assets (manual redirect + Range resume + retries)."""
import ssl, socket, sys, time, os, re

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
CTX = ssl.create_default_context()


def conn(host, port=443, timeout=30):
    s = socket.create_connection((host, port), timeout=timeout)
    return CTX.wrap_socket(s, server_hostname=host)


def parse_url(url):
    m = re.match(r'https://([^/]+)(/.*)?$', url)
    host = m.group(1)
    path = m.group(2) or '/'
    return host, path


def get_headers(host, path, start=0, timeout=30):
    s = conn(host, timeout=timeout)
    rng = ('Range: bytes=%d-\r\n' % start) if start else ''
    req = ('GET %s HTTP/1.1\r\nHost: %s\r\nUser-Agent: %s\r\nAccept: */*\r\n%sConnection: close\r\n\r\n'
           % (path, host, UA, rng))
    s.sendall(req.encode())
    buf = b''
    while b'\r\n\r\n' not in buf:
        c = s.recv(4096)
        if not c:
            raise IOError('connection closed while reading headers')
        buf += c
        if len(buf) > 65536:
            raise IOError('header too large')
    head, rest = buf.split(b'\r\n\r\n', 1)
    return s, head.decode('latin1'), rest


def download(url, out, expected=None):
    host, path = parse_url(url)
    # resolve redirect
    for _ in range(6):
        s, head, rest = get_headers(host, path, 0)
        status = int(head.split(' ')[1])
        if status in (301, 302, 303, 307, 308):
            loc = re.search(r'(?im)^Location:\s*(\S+)', head).group(1)
            s.close()
            host, path = parse_url(loc)
            url = loc
            continue
        break
    else:
        raise IOError('too many redirects')

    s.close()
    # ranged download loop
    done = os.path.getsize(out) if os.path.exists(out) else 0
    fatal = 0
    while True:
        try:
            s, head, rest = get_headers(host, path, done)
            status = int(head.split(' ')[1])
            if status not in (200, 206):
                raise IOError('HTTP %d' % status)
            m = re.search(r'(?i)content-range:\s*bytes\s+(\d+)-(\d+)/(\d+)', head)
            if m:
                total = int(m.group(3))
            elif expected:
                total = expected
            else:
                m2 = re.search(r'(?i)content-length:\s*(\d+)', head)
                total = done + int(m2.group(1))
            if status == 200 and done:
                # server ignored range -> restart
                done = 0
                s.close()
                continue
            with open(out, 'ab') as f:
                if rest:
                    f.write(rest)
                    done += len(rest)
                last = time.time()
                while True:
                    b = s.recv(1 << 18)
                    if not b:
                        break
                    f.write(b)
                    done += len(b)
                    if time.time() - last > 3:
                        pct = 100.0 * done / total if total else 0
                        print('  %.1f%%  %d/%d' % (pct, done, total), flush=True)
                        last = time.time()
            s.close()
            if done >= total:
                print('  done %d/%d' % (done, total), flush=True)
                return done
            print('  short read %d/%d, resuming' % (done, total), flush=True)
        except Exception as e:
            fatal += 1
            print('  retry %d after %s: %s' % (fatal, type(e).__name__, e), flush=True)
            if fatal > 40:
                raise
            time.sleep(min(2 + fatal, 10))


if __name__ == '__main__':
    url, out = sys.argv[1], sys.argv[2]
    exp = int(sys.argv[3]) if len(sys.argv) > 3 else None
    n = download(url, out, exp)
    print('FINAL', n)
