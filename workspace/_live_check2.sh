#!/bin/sh
python - <<'EOF' 2>/dev/null || true
EOF
echo "=== 条目数与最后 3 条 ==="
awk '/"date"/{n++} END{print "entries:", n}' /dobot/userdata/project/settings/function/homeEncoder.json
tail -c 1200 /dobot/userdata/project/settings/function/homeEncoder.json
echo
echo "=== 文件的修改时间 ==="
ls -la /dobot/userdata/project/settings/function/homeEncoder.json
echo "=== 现在时间 ==="
date
