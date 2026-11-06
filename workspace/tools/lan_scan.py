# -*- coding: utf-8 -*-
"""扫本机所在 /24 网段上的 Dobot 设备特征端口，确认控制箱是否已接入。"""
import socket, ipaddress, subprocess, concurrent.futures as cf, re, sys

def local_v4():
    out = subprocess.run(["ipconfig"], capture_output=True, text=True, encoding="gbk", errors="replace").stdout
    ips = []
    for m in re.finditer(r"IPv4[^:]*:\s*([0-9.]+)", out):
        ips.append(m.group(1))
    return [ip for ip in ips if not ip.startswith("127.")]

def probe(ip, port, t=0.35):
    s = socket.socket(); s.settimeout(t)
    try:
        s.connect((ip, port)); return True
    except Exception:
        return False
    finally:
        s.close()

PORTS = [29999, 22, 8080, 445]
targets = []
for ip in local_v4():
    targets += [(str(h), p) for h in ipaddress.ip_network(ip + "/24", strict=False).hosts() for p in PORTS]

print("本机 IPv4:", local_v4())
print(f"扫描 {len(targets)} 个 (ip, port) 组合 …")
found = []
with cf.ThreadPoolExecutor(max_workers=256) as ex:
    for (ip, port), ok in zip(targets, ex.map(lambda a: probe(*a), targets)):
        if ok:
            found.append((ip, port))

by_ip = {}
for ip, port in found:
    by_ip.setdefault(ip, []).append(port)
print("\n--- 有响应的主机 ---")
for ip, ports in sorted(by_ip.items()):
    tag = ""
    if 29999 in ports: tag = "  <= Dobot TCP 控制端口，很可能是控制箱"
    elif 445 in ports and 22 in ports: tag = "  (Windows/Samba 主机)"
    print(f"  {ip:15} 开放 {sorted(ports)}{tag}")
if not by_ip:
    print("  （无）")

print("\n--- 直连 192.168.5.1 复测 ---")
for p in [22, 29999, 8080, 4840]:
    print(f"  192.168.5.1:{p} -> {'OPEN' if probe('192.168.5.1', p, 0.6) else 'unreachable'}")
