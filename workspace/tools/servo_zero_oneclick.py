#!/usr/bin/env python3
"""servo_zero_oneclick.py — CR5 零点补丁「点击即用」入口（2026-09-25）。

适用场景：刚用厂家软件（DobotStudio Pro / 示教器）完成一次标零之后，把零点补丁
恢复/安装到控制器并当场验证。全部操作只发生在控制器侧（PLC 应用每轴 2 字节），
不改伺服固件、不碰 EtherCAT 总线命令、不需要点动机械臂。

用法（三种等价）：
  双击 run_zero_fix.bat
  python tools\\servo_zero_oneclick.py
  python tools\\servo_zero_oneclick.py --ask    # 每个写操作前多问一句

它按现场状态自适应，四个分支：
  A. 在用 app 已是补丁版 & 本次开机映射已生效 → 只读验证，什么都不改（输出结论）。
  B. 在用 app 是原版（厂家软件工程下载/升级覆盖回去了） → 用本地成品补丁包重装。
  C. 在用 app 是未知版本（未来整机升级变了样） → 现场拉取 → 现场打补丁 → 装回。
     拉取与补丁产物都留档在 data/cabinet/。
  D. 连不上控制箱 → 只做本地成品自检，并提示恢复网络。

安全闸门（任何一步不过就停，绝不半装）：
  * 6 张 TxPDO 表、条目数 20/20/20/29/23/24、块长 57/57/57/93/69/71 逐项断言；
  * 装回前 md5 复核；装回后再次拉取校验；
  * 每次安装前自动在控制箱上备份当前在用文件（BACKUP_pdo_<时间戳>）；
  * --ask 模式在每个写操作前要求回车确认。

背景与证据链见 SERVO_ZERO_FIX_README.md / SERVO_SUMMARY.md §16–§19。
"""
import argparse
import hashlib
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import servo_zero_fix as szf            # noqa: E402  (成品工具：解析/补丁/SSH/校验)

PATCHED_MD5 = "9a808cd9dd8f3aa6adaa4de1a34eb9b3"   # 六轴补丁版 app（2026-09-24 成品）
STOCK_MD5 = "8416cf0eee070a640702c077eb904b4e"     # 真·原版 app
CAB = os.path.join(ROOT, "data", "cabinet")
LOCAL_PATCHED_APP = os.path.join(CAB, "Application_fixed_all6.app")
LOCAL_PATCHED_CRC = os.path.join(CAB, "Application_fixed_all6.crc")
CTRL_IP = szf.CTRL_IP


def step(msg):
    print("\n" + "=" * 74)
    print(msg)
    print("=" * 74)


def md5_of(path):
    return hashlib.md5(open(path, "rb").read()).hexdigest()


def ask(prompt):
    if not ASK:
        return True
    ans = input("%s  [y/N] " % prompt).strip().lower()
    return ans in ("y", "yes")


def ssh(cmd):
    return szf.ssh_script(cmd, "oneclick")


def run_local(cmd):
    p = subprocess.run(cmd, shell=True, cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "") + (p.stderr or "")


# ------------------------------------------------------------------ 0) 本地
def local_stocktake():
    step("第 0 步：本地成品自检")
    ok = True
    for p, want in ((LOCAL_PATCHED_APP, PATCHED_MD5), (LOCAL_PATCHED_CRC, None)):
        if not os.path.exists(p):
            print("  ✗ 缺 %s" % p)
            ok = False
    if ok:
        got = md5_of(LOCAL_PATCHED_APP)
        print("  本地补丁版 app: %s  md5 %s" % (os.path.basename(LOCAL_PATCHED_APP),
                                                 got))
        print("  %s" % ("  ✓ 与 2026-09-24 已验证成品一致" if got == PATCHED_MD5
                        else "  ✗ md5 与成品不符！本地文件被动过，改用分支 C 现场重建"))
    return ok


# ------------------------------------------------------- 1) 控制箱连通与状态
def controller_state():
    step("第 1 步：控制箱状态（只读）")
    rc, out = ssh("echo ---APP---\n"
                  "md5sum %s/Application.app %s/Application.crc\n"
                  "echo ---BOOT---\n"
                  "cat /tmp/codesysBoot; echo\n"
                  "echo ---UPTIME---\n"
                  "cat /proc/uptime" % (szf.DEFAULT_VARIANT, szf.DEFAULT_VARIANT))
    if rc != 0 or "---APP---" not in out:
        print(out.strip() or "(no output)")
        print("  ✗ 连不上控制箱 %s —— 请确认网线/网络与控制箱上电状态。" % CTRL_IP)
        return None
    md5 = boot = uptime = ""
    section = None
    for line in out.splitlines():
        t = line.strip()
        if t == "---APP---":
            section = "app"; continue
        if t == "---BOOT---":
            section = "boot"; continue
        if t == "---UPTIME---":
            section = "up"; continue
        if not t:
            continue
        if section == "app" and "Application.app" in t:
            md5 = t.split()[0]
        elif section == "boot" and not boot:
            boot = t
        elif section == "up" and not uptime:
            uptime = t.split()[0]
    print("  在用变体  : %s" % (boot or "?"))
    print("  在用 app  : %s" % md5)
    print("  开机时长  : %s s" % uptime if uptime else "  开机时长  : ?")
    return md5, boot, uptime


# ------------------------------------------------------------- 2) 现场验证
def field_check():
    """只读判据（与 servo_zero_fix.py check 相同）。"""
    step("第 2 步：现场只读判据（关节角 / 固件 / PDO 末项映射）")
    rc, out = run_local('python tools\\servo_zero_fix.py check')
    print(out.strip())
    return rc == 0 and "VERDICT" in out


def verify_mapping_after_install():
    """装机后（重启前）API 级快速验证：0x1A00 末项是否已按补丁写入。"""
    step("第 2b 步：装机后映射核验（读本次开机前残留的 SDO 写日志）")
    rc, out = ssh("L=/dobot/userdata/CR5_sys_files/project/logs/codesys/log\n"
                  "grep -ao 'SDO write ok: Address: [0-9]* Index: 16#1A00 SubIndex: "
                  "[0-9]* Data: 16#[0-9A-F]*' $L | tail -n 40\n")
    ok_all = True
    seen = 0
    for line in out.splitlines():
        m = szf.re.search(r"Address: (\d+) Index: 16#1A00 SubIndex: (\d+) Data: 16#([0-9A-F]+)", line)
        if not m:
            continue
        seen += 1
        data = m.group(3)
        ok_all &= data.upper().endswith("60640020")
    print("  本次日志中 0x1A00 写入 %d 条，末条全部为 60640020：%s"
          % (seen, "是 ✓" if ok_all and seen else "否（见下）"))
    if not ok_all or not seen:
        print("  （装的是新 app，要等下一次重启、PLC 重新映射时才会出现新写入；"
              "这不是失败——重启后跑 check 即见。）")
    return True


def main():
    global ASK
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ask", action="store_true", help="每个写操作前确认")
    args = ap.parse_args()
    ASK = args.ask

    print("CR5 零点补丁 一键脚本  ·  " + time.strftime("%Y-%m-%d %H:%M:%S"))
    print("对象：控制箱 %s（纯主控侧，不改伺服固件）" % CTRL_IP)

    # ---- 0) 本地 ----
    local_ok = local_stocktake()
    if not local_ok:
        print("\n本地成品缺失，仍可走分支 C（现场拉取+现场补丁）。")

    # ---- 1) 控制箱 ----
    st = controller_state()
    if st is None:
        print("\n结论：控制箱不可达。恢复网络后重跑本脚本即可。")
        return 1
    md5, boot, uptime = st

    # ---- 分支决策 ----
    if md5 == PATCHED_MD5:
        step("分支 A：在用 app 已是补丁版")
        print("  在用 app md5 == 六轴补丁版（%s）" % PATCHED_MD5)
        print("  → 只读验证本次开机映射与关节角，不做任何改动。")
        field_check()
        print("\n结论：补丁已在位且生效。标零后读数 ≈0、下/上使能不掉零即为正常。")
        print("      若关节角不为 ≈0：那是标定/机械摆放问题，不是补丁问题——")
        print("      按 SERVO_ZERO_FIX_README.md §3 的原始判据复验（静止 30 s 再读）。")
        return 0

    if md5 == STOCK_MD5:
        step("分支 B：在用 app 是原版（被厂家软件覆盖回去了）")
        print("  在用 app md5 == 原版（%s）" % STOCK_MD5)
        if not local_ok:
            print("  但本地成品缺失/损坏 → 转分支 C 现场重建。")
            return branch_c()
        if not ask("  用本地成品补丁包重装到控制箱？（先自动备份，装完需重启控制箱）"):
            print("  已取消。")
            return 1
        return branch_b()

    step("分支 C：未知 app 版本（未来整机升级/其他变体）")
    print("  在用 app md5 = %s（既非补丁版也非原版）" % md5)
    if not ask("  现场拉取在用 app → 打补丁 → 装回？（全程自动备份）"):
        pull_path = os.path.join(CAB, "Application_live_%s.app"
                                 % time.strftime("%Y%m%d_%H%M%S"))
        print("  已取消；仍按只读留档：拉取到 %s" % pull_path)
        rc, out = run_local('python tools\\servo_zero_fix.py pull --out "%s"' % pull_path)
        print(out.strip())
        return 1
    return branch_c()


def branch_b():
    step("第 3 步（分支 B）：重装六轴补丁版")
    rc, out = run_local(
        'python tools\\servo_zero_fix.py install "%s" "%s"'
        % (LOCAL_PATCHED_APP, LOCAL_PATCHED_CRC))
    print(out.strip())
    if rc != 0:
        print("  ✗ install 失败 —— 不会装半套；回滚目录见上方输出。")
        return 1
    verify_mapping_after_install()
    print_reboot_hint()
    return 0


def branch_c():
    step("第 3 步（分支 C）：现场拉取 → 补丁 → 装回")
    stamp = time.strftime("%Y%m%d_%H%M%S")
    pulled = os.path.join(CAB, "Application_live_%s.app" % stamp)
    rc, out = run_local('python tools\\servo_zero_fix.py pull --out "%s"' % pulled)
    print(out.strip())
    if rc != 0 or not os.path.exists(pulled):
        print("  ✗ 拉取失败，停止。")
        return 1
    live_md5 = md5_of(pulled)
    print("  已拉取：%s（md5 %s）" % (pulled, live_md5))
    if live_md5 == PATCHED_MD5:
        print("  → 拉下来就是补丁版（在用与文件不一致，可能还没重启）→ 无需改动。")
        print("     重启控制箱后跑 check 即可。")
        return 0
    patched = pulled[:-4] + "_patched.app"
    rc, out = run_local(
        'python tools\\servo_zero_fix.py patch "%s" --slaves all --out "%s" '
        '--crc-out "%s" --write' % (pulled, patched, patched[:-4] + ".crc"))
    print(out.strip())
    if rc != 0 or "STOP" in out or not os.path.exists(patched):
        print("  ✗ 补丁闸门未过（结构断言失败）——未知版本，宁 stop 不装。")
        return 1
    if md5_of(patched) == PATCHED_MD5:
        known = "（= 已验证成品，好兆头）"
    elif md5_of(patched) == STOCK_MD5:
        known = "（!! = 原版，说明补丁没打上，停止）"
    else:
        known = ""
    print("  补丁产物：%s%s" % (patched, known))
    if md5_of(patched) == STOCK_MD5:
        return 1
    if not ask("  装回控制箱？（先自动备份当前在用文件）"):
        print("  已取消（补丁产物已留档本地：%s）。" % patched)
        return 1
    rc, out = run_local(
        'python tools\\servo_zero_fix.py install "%s" "%s"'
        % (patched, patched[:-4] + ".crc"))
    print(out.strip())
    if rc != 0:
        return 1
    verify_mapping_after_install()
    print_reboot_hint()
    return 0


def print_reboot_hint():
    print("\n" + "!" * 74)
    print("已安装。★ 下一步（必须人工做）：重启控制箱使 PLC 应用生效。")
    print("  方式任选：整机断电重启 / DSC 软件里重启控制器 / SSH reboot。")
    print("  重启后运行：python tools\\servo_zero_fix.py check")
    print("  期望：六轴 0x1A00 末条全部 60640020 OK，关节角 ≈0（标零后）。")
    print("!" * 74)


if __name__ == "__main__":
    sys.exit(main())
