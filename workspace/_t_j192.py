import socket
import struct

HOST = "192.168.5.1"
PORT = 30005

s = socket.create_connection((HOST, PORT), timeout=5)
data = b""
while len(data) < 1440:
    chunk = s.recv(1440 - len(data))
    if not chunk:
        break
    data += chunk
s.close()
print("got", len(data), "bytes")

vals = struct.unpack_from("<45d", data, 0)
print("real joints (offset 192+8*i):")
for i in range(6):
    v = vals[24 + i]  # 192/8 = 24
    print("  J%d = %+.6f" % (i + 1, v))
counts6 = vals[29] / (360.0 / (20000 * 101))
print("J6 raw counts equivalent = %.1f" % counts6)
