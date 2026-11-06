
import re, sys
p = r'D:\software\dobot\V1.3.4-stable\RobotMaintenanceTools.exe'
data = open(p,'rb').read()
print("size", len(data))
def asc(b, n=6):
    return re.findall(rb'[\x20-\x7e]{%d,}' % n, b)
def u16(b, n=4):
    return re.findall(rb'(?:[\x20-\x7e]\x00){%d,}' % n, b)
kw = [b'password', b'Password', b'PASSWORD', b'passwd', b'verify', b'Verify', b'random', b'Random',
      b'secret', b'Secret', b'token', b'license', b'License', b'activation', b'Activation',
      b'crypt', b'Crypt', b'aes', b'AES', b'md5', b'MD5', b'sha', b'SHA', b'base64', b'Base64',
      b'key', b'Key', b'code', b'Code', b'sn', b'SN']
for k in kw:
    hits = [m.start() for m in re.finditer(re.escape(k), data)]
    if hits:
        print("%-12s x%d   first@%d" % (k.decode(), len(hits), hits[0]))
print()
print("--- ASCII 串中含 password/pass/key/verify 的 ---")
seen=set()
for s in asc(data, 5):
    t = s.decode('latin-1')
    if re.search(r'pass|Pass|PASS|verify|Verify|secret|Secret|random|Random|license|License|激活|授权', t) and t not in seen:
        seen.add(t)
        if len(t) < 120:
            print("  ", t)
    if len(seen) > 60: break
