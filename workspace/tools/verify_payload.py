# -*- coding: utf-8 -*-
"""按 manifest 声明的口径校验固件包：载荷 = 文件去掉 32 字节头。"""
import hashlib, pathlib
B = pathlib.Path(r"D:\mydata\working things\机械臂控制柜数据")

def check(name, path, expect_payload_md5, expect_len):
    blob = path.read_bytes()
    payload = blob[32:]
    md5 = hashlib.md5(payload).hexdigest()
    print(f"{name}")
    print(f"   文件            {len(blob)} B")
    print(f"   载荷            {len(payload)} B   期望 {expect_len}  -> {'MATCH' if len(payload)==expect_len else 'MISMATCH'}")
    print(f"   载荷 MD5        {md5}")
    print(f"   manifest 声明   {expect_payload_md5}  -> {'MATCH' if md5==expect_payload_md5 else 'MISMATCH'}")
    print(f"   头 32B          {blob[:32].hex()}")

check("CR5_Servo_ST_FOE_V3.1.5.0_UNVERIFIED.bin",
      B / "3.1.5_candidate_upgrade" / "CR5_Servo_ST_FOE_V3.1.5.0_UNVERIFIED.bin",
      "f4f8d656fc02488bd946112c6130d068", 328860)

check("CR5_Servo_ST_FOE_V3.2.D.8_REBUILT.bin",
      pathlib.Path(r"D:\mydata\workspace\servo_fw\CR5_Servo_ST_FOE_V3.2.D.8_REBUILT.bin"),
      "0f5d836c1d99998a4146b3e71e6f04ff", 338072)
