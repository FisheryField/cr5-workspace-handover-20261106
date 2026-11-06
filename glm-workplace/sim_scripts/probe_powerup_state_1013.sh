#!/bin/sh
# probe_powerup_state_1013.sh — 按柜开关后机械臂不通电：探柜内主控日志+伺服电压监控通道
# 只读诊断，不写任何东西。
echo "===== [1] uptime / 当前时间 ====="
uptime
date

echo "===== [2] codesysBoot 尾部（主控启动自检） ====="
tail -n 30 /tmp/codesysBoot 2>/dev/null || echo "(no /tmp/codesysBoot)"

echo "===== [3] 柜内日志尾部 40 行 ====="
tail -n 40 /dobot/userdata/CR5_sys_files/project/logs/all/log 2>/dev/null || echo "(no all/log)"

echo "===== [4] 伺服电源相关进程（ethercat/codesys/servo） ====="
ps | grep -Ei 'codesys|ethercat|servo' | grep -v grep

echo "===== [5] EtherCAT 状态（退 OP=60945 那套） ====="
ls /sys/class/ethercat 2>/dev/null || echo "(no /sys/class/ethercat)"
cat /proc/ethercat 2>/dev/null | head -n 20 || true

echo "===== [6] 28422 伺服电源监控通道（uiBodyVolt 之类） ====="
# 3rd-party dashboard 通道：3 秒采样，看伺服母线电压是否建立
python3 - <<'EOF'
import socket, json, time
def fetch():
    try:
        s = socket.create_connection(("127.0.0.1", 28422), timeout=2)
        s.settimeout(2)
        buf = b""
        t0 = time.time()
        while time.time() - t0 < 2.5:
            d = s.recv(65536)
            if not d: break
            buf += d
        s.close()
        return buf.decode("utf-8", "ignore")
    except Exception as e:
        return "ERR:" + repr(e)

raw = fetch()
open("/tmp/probe_28422_1013.txt", "w").write(raw)
keys = ("uiBodyVolt", "BodyVolt", "ServoVolt", "PowerVolt", "io_in_status",
        "servo_ready", "ServoEnable", "Emergency", "ESTOP", "estop", "safety")
found = {}
for ln in raw.splitlines():
    for k in keys:
        if k in ln:
            found.setdefault(k, []).append(ln.strip()[:220])
print("raw_len:", len(raw))
for k, v in found.items():
    print("--", k, "->", len(v), "hits; sample:", v[-1] if v else "")
EOF

echo "===== [7] 本轮 python 探针出错时留痕 ====="
ls -l /tmp/probe_28422_1013.txt 2>/dev/null && head -c 400 /tmp/probe_28422_1013.txt | tr -d '\0' | head -n 5

echo "===== [8] 完 ====="
