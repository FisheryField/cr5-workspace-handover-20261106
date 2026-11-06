# -*- coding: utf-8 -*-
import zipfile, struct, pathlib
ZIP = pathlib.Path(r"D:\mydata\working things\CR5_CC162_V3.5.4.1-stable-a014bd6f-2212301029_20260916_Backup.zip")
with zipfile.ZipFile(ZIP) as z:
    for i in z.infolist():
        print(f"name={i.filename}")
        print(f"  flag_bits=0x{i.flag_bits:04x}  encrypted={bool(i.flag_bits & 0x1)}  compress_type={i.compress_type}")
        print(f"  date={i.date_time}  crc=0x{i.CRC:08x}  size={i.file_size}  compress_size={i.compress_size}")
        # 压缩方法 99 = AES (WinZip AE-x)
        print(f"  -> {'AES/WinZip 加密' if i.compress_type == 99 else 'ZipCrypto (传统加密)'}")
        # 额外字段里若含 0x9901 即 AES
        for tag, ln in struct.iter_unpack("<HH", i.extra[: len(i.extra) // 4 * 4] or b"\x00\x00\x00\x00"):
            if tag == 0x9901:
                print("  extra 0x9901 存在 -> 确认 WinZip AES")

CANDS = ["dobot", "888888", "123456", "dobot123", "Dobot123", "admin", "1234567890", "dobot2026"]
with zipfile.ZipFile(ZIP) as z:
    name = z.namelist()[0]
    for c in CANDS:
        try:
            with z.open(name, pwd=c.encode()) as f:
                head = f.read(4)
            print(f"  口令 {c!r:14} -> 解出前 4 字节 {head.hex()}  (gzip 魔数应为 1f8b)")
            if head[:2] == b"\x1f\x8b":
                print(f"  *** 命中口令: {c} ***")
                break
        except Exception as e:
            print(f"  口令 {c!r:14} -> {type(e).__name__}: {e}")
