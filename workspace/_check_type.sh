echo "=== 今天所有 singleFwAndXml 请求及其 type ==="
grep -a -E "2026-09-22 .*(type:|request update type)" /mToolServer/mToolServer.log 2>/dev/null | grep -a -E "type:" | tail -20
echo
echo "=== 今天所有 FoE 固件写入记录 ==="
grep -a "2026-09-22" /mToolServer/mToolServer.log 2>/dev/null | grep -a -E "updateSlaveFW|start FoE write|filesize=" | tail -20
echo
echo "=== 今天所有 updateSlaveXml / updateSlaveFW 调用 ==="
grep -a "2026-09-22" /mToolServer/mToolServer.log 2>/dev/null | grep -a -oE "2026-09-22 [0-9:.]+.*(updateSlaveXml|updateSlaveFW)\(\)#[0-9]+][^\"]{0,60}" | tail -20
echo
echo "=== 控制器恢复确认 ==="
date; cat /proc/uptime
ps | grep -E "codesys|gcontrol" | grep -v grep
echo
echo "=== 当前版本 JSON ==="
curl -s -X POST http://127.0.0.1:22000/settings/version 2>/dev/null | tr -d ' \t' | grep -E "servo|control"
