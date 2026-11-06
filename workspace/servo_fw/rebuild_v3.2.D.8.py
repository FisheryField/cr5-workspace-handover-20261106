# -*- coding: utf-8 -*-
"""从 servo_hex_comparison 的 Intel HEX 重建原厂 CR5_Servo_ST_FOE_V3.2.D.8.bin。

32 字节 FoE 头结构（由 3.1.5_candidate_upgrade/manifest.json 的 reference 头推得）:
  d4c3b2a1 | MD5(payload) 16B | length LE32 | 08 00 00 00 | ff ff ff ff
判据: 重建结果整体 MD5 必须等于原厂值 8f5a1901152c8d300f2b2030603eaa16
"""
import hashlib, json, struct, sys, pathlib

HEX = pathlib.Path(r"D:\mydata\working things\机械臂控制柜数据\servo_hex_comparison\CR5_Servo_ST_FOE_V3.2.D.8_APP_08010000.hex")
OUT = pathlib.Path(r"D:\mydata\workspace\servo_fw\CR5_Servo_ST_FOE_V3.2.D.8_REBUILT.bin")
BASE, LAST = 0x08010000, 0x08062897          # manifest 声明范围（含末地址）
EXPECT_FILE_MD5 = "8f5a1901152c8d300f2b2030603eaa16"   # result.md 记录的原厂文件 MD5
EXPECT_HDR_PAYLOAD_MD5 = bytes.fromhex("0f5d836c1d99998a4146b3e71e6f04ff")  # manifest 记录的 reference 头内 MD5

mem, upper, bad, recs = {}, 0, [], 0
for raw in HEX.read_text().splitlines():
    line = raw.strip()
    if not line or not line.startswith(":"):
        continue
    b = bytes.fromhex(line[1:])
    n, addr, typ, data = b[0], (b[1] << 8) | b[2], b[3], b[4:4 + b[0]]
    if (sum(b) & 0xFF) != 0:
        bad.append(("checksum", line))
        continue
    recs += 1
    if typ == 0x00:
        for i, v in enumerate(data):
            a = upper + addr + i
            if a in mem and mem[a] != v:
                bad.append(("conflict", hex(a)))
            mem[a] = v
    elif typ == 0x04:
        upper = struct.unpack(">H", data)[0] << 16
    elif typ in (0x01, 0x02, 0x03, 0x05):
        pass
    else:
        bad.append(("rectype", typ))

lo, hi = min(mem), max(mem)
print(f"HEX 记录数 {recs}；地址范围 {hex(lo)}—{hex(hi)}；字节数 {len(mem)}；异常 {bad[:5]}")

size = LAST - BASE + 1
payload = bytes(mem.get(BASE + i, 0xFF) for i in range(size))
print(f"载荷 {len(payload)} B  期望 {size} B")

pay_md5 = hashlib.md5(payload).digest()
print(f"载荷 MD5          : {pay_md5.hex()}")
print(f"reference 头内 MD5: {EXPECT_HDR_PAYLOAD_MD5.hex()}  -> {'MATCH' if pay_md5 == EXPECT_HDR_PAYLOAD_MD5 else 'MISMATCH'}")

header = bytes.fromhex("d4c3b2a1") + pay_md5 + struct.pack("<I", len(payload)) + bytes.fromhex("08000000ffffffff")
blob = header + payload
file_md5 = hashlib.md5(blob).hexdigest()
print(f"重建文件大小: {len(blob)} B  期望 338104 B -> {'MATCH' if len(blob) == 338104 else 'MISMATCH'}")
print(f"重建文件 MD5 : {file_md5}")
print(f"原厂文件 MD5 : {EXPECT_FILE_MD5}  -> {'*** 完全一致 ***' if file_md5 == EXPECT_FILE_MD5 else '不一致'}")

if file_md5 == EXPECT_FILE_MD5:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(blob)
    (OUT.parent / "CR5_Servo_ST_FOE_V3.2.D.8_REBUILT.json").write_text(json.dumps({
        "file": OUT.name, "bytes": len(blob), "md5": file_md5,
        "header_hex": header.hex(), "payload_bytes": len(payload),
        "payload_md5": pay_md5.hex(),
        "payload_md5_in_original_header": EXPECT_HDR_PAYLOAD_MD5.hex(),
        "source_hex": str(HEX), "source_hex_sha256": hashlib.sha256(HEX.read_bytes()).hexdigest(),
        "expected_vendor_md5": EXPECT_FILE_MD5,
        "verified": "MD5 of rebuilt file equals vendor-recorded MD5; payload MD5 equals the MD5 embedded in the vendor header",
        "provenance": "Built from a byte-exact re-encoding of the vendor file's application region; do not treat as an independent vendor copy."
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print("已写出:", OUT)
else:
    sys.exit(2)
