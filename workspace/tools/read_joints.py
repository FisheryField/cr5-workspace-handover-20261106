#!/usr/bin/env python3
"""Read the CR5 realtime feedback stream to get the actual joint values.

This is the SAME thing the vendor tool does (mToolServer logs
"connect port 30005 success" then "date length:1440"), and it is read-only.
Port 30005 is the 125 Hz feedback stream; the packet is 1440 bytes and the
six joint positions are float64 starting at byte offset 32.
"""
import socket
import struct
import sys

HOST, PORT = "192.168.5.1", 30005
NAMES = ["J1", "J2", "J3", "J4", "J5", "J6"]


def main():
    s = socket.create_connection((HOST, PORT), timeout=8)
    buf = b""
    while len(buf) < 1440:
        chunk = s.recv(4096)
        if not chunk:
            break
        buf += chunk
    s.close()
    print("received %d bytes" % len(buf))
    if len(buf) < 1440:
        print("!! short packet - stream did not deliver 1440 bytes")
        return 2

    hdr = struct.unpack_from("<4Q", buf, 0)
    print("header u64 x4 : %s" % (hdr,))
    print()
    for label, off in (("q_actual  (offset 32)", 32),
                       ("q_target  (offset 128)", 128),
                       ("next      (offset 224)", 224)):
        vals = struct.unpack_from("<6d", buf, off)
        print("%s :" % label)
        for n, v in zip(NAMES, vals):
            print("    %s = %12.6f" % (n, v))
        print()
    print("J6 raw counts equivalent (deg / (360/(20000*101))) = %.0f"
          % (struct.unpack_from("<d", buf, 32 + 5 * 8)[0] / (360.0 / (20000 * 101))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
