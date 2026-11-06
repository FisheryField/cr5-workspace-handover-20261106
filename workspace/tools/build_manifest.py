# -*- coding: utf-8 -*-
"""为 workspace\data 生成带 SHA-256 的数据清单，并登记工作区外的引用与已丢失资产。"""
import hashlib, json, os, pathlib, datetime

WS = pathlib.Path(r"D:\mydata\workspace")
DATA = WS / "data"

PROV = {  # 相对 data/ 的前缀 -> 来源与性质
    "cabinet/3.1.5.hex": ("Dobot 伺服 V3.1.5.0 整片 flash 转储", "现场从驱动器读出"),
    "cabinet/3.1.5_candidate_upgrade": ("自制 FoE 包（3.1.5.0 同版本候选）", "自制，未上机验证过跨版本"),
    "cabinet/servo_hex_comparison": ("原厂 3.2.D.8 应用区 hex 与其清单", "由原厂 bin 派生"),
    "cabinet/CR_update_V3.5.4.1": ("控制器升级包 3.5.4.1", "Dobot 原厂"),
    "cabinet/CR_update_V3.5.4.2": ("控制器升级包 3.5.4.2", "Dobot 原厂"),
    "cabinet/dobot_upgrade_observation": ("9/16 J1 原厂同版本升级观察记录", "现场记录"),
    "backup_20260916": ("9/16 /dobot/userdata/project 备份解压内容", "现场 tar 备份，zip 口令 dobot123"),
    "servo_rebuilt": ("重建的原厂 3.2.D.8 固件", "由应用区 hex 重建，MD5 与原厂一致"),
    "official": ("官方 3.5.4.1 / 3.5.6.1 升级材料（伺服固件、PDO XML、伺服参数表、upgrade.ini）", "Dobot 原厂；固件 SHA-256 与旧 manifest 记录的原厂参考值一致"),
}

def sha256(p, buf=1 << 20):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while (b := f.read(buf)):
            h.update(b)
    return h.hexdigest()

entries = []
for root, dirs, files in os.walk(DATA):
    dirs[:] = [d for d in dirs if d != "__pycache__"]
    for fn in sorted(files):
        p = pathlib.Path(root) / fn
        rel = p.relative_to(DATA).as_posix()
        entries.append({
            "path": rel,
            "bytes": p.stat().st_size,
            "sha256": sha256(p),
            "mtime": datetime.datetime.fromtimestamp(p.stat().st_mtime).isoformat(timespec="seconds"),
        })

def prov_for(rel):
    for k, v in PROV.items():
        if rel.startswith(k):
            return {"what": v[0], "origin": v[1]}
    return {"what": "未分类", "origin": "未知"}

for e in entries:
    e.update(prov_for(e["path"]))

# servo_fw 里的重建固件也纳入
sf = WS / "servo_fw" / "CR5_Servo_ST_FOE_V3.2.D.8_REBUILT.bin"
if sf.exists():
    entries.append({
        "path": "../servo_fw/" + sf.name, "bytes": sf.stat().st_size, "sha256": sha256(sf),
        "mtime": datetime.datetime.fromtimestamp(sf.stat().st_mtime).isoformat(timespec="seconds"),
        "what": "重建的原厂 CR5 伺服固件 V3.2.D.8（可上机 FoE 镜像）",
        "origin": "由 3.2.D.8 应用区 hex + 32 字节 FoE 头重建；整文件 MD5 8f5a1901152c8d300f2b2030603eaa16 与原厂记录一致",
        "md5": hashlib.md5(sf.read_bytes()).hexdigest(),
    })

manifest = {
    "generated": datetime.datetime.now().isoformat(timespec="seconds"),
    "note": "工作区内的权威数据副本。工作区外同名目录见 external_refs，回收站副本经比对为逐字节重复，无独有内容。",
    "file_count": len(entries),
    "total_bytes": sum(e["bytes"] for e in entries),
    "files": entries,
    "external_refs": [
        {"path": r"D:\mydata\working things\机械臂控制柜数据", "relation": "data/cabinet 的来源（已完整复制）"},
        {"path": r"D:\mydata\working things\dobot_arm", "relation": "RoboDK 工程 / ROS 包 / 手册，与本任务无直接关系，未纳入"},
        {"path": r"D:\mydata\workspace-旧版数据", "relation": "旧工作区冷备（内容已并入本工作区根目录）"},
        {"path": r"D:\$RECYCLE.BIN\S-1-5-21-3003449410-212866346-2127617813-1001\$RRT678O", "relation": "9/21 10:17 D:\mydata 被换下时的快照；与活动目录逐文件一致，无独有内容"},
    ],
    "lost_assets": [
        r"D:\software\DobotStudio\V1.3.4-stable\V1.3.4-stable\upgradeFiles\3.5.6\3.5.6.1\files\CR_Servo_ST_XML_V3.0.0.bin",
        r"...\servoCSV\CR\CR5\J1.csv ~ J6.csv",
        r"...\servoCSV\CR\param.csv",
        r"...\files\CR5_Servo_ST_FOE_V4.1.4.0.bin",
        r"...\files\CR_TerminalIO_ST_FOE_V3.3.5.0.bin 等其余从站固件",
        r"...\3.5.6.1upgrade.ini",
        r"...\3.5.6.1detailChinese.txt",
        "→ 全盘与回收站均已确认不存在；需从 DobotStudio Pro 重新获取",
    ],
}

out = DATA / "manifest.json"
out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"写出 {out}")
print(f"收录 {manifest['file_count']} 个文件, {manifest['total_bytes']:,} B")
for e in entries[:0]:
    pass
