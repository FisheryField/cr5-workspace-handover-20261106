# -*- coding: utf-8 -*-
# 给 HANDOVER.md（另一会话 12:00 归档）插入过期横幅，防止新会话误读旧结论
import io

p = r'D:\mydata\glm-workplace\HANDOVER.md'
s = io.open(p, encoding='utf-8').read()
if 'CHECKPOINT_v37' in s:
    print('banner already present, skip')
    raise SystemExit(0)

anchor = '> 归档：2026-09-28 ｜ 自包含 ✅ —— 不需要读之前的会话或其它目录'
banner = '''

> ⚠️ **2026-09-28 14:45 横幅（另一会话后加）**——本档写于 12:00，以下结论已过期：
> ① "伺服最终必须是 3.1.5.0" → 用户已自刷 **3.2.d.8**（14:21 起生效），14:32:44 使能成功且健康；
> ② "零点已修好" → 12:01 使能仍翻系+0x86（档案恢复方案判死）；
> ③ 坐标判据已换新系（稳定 92.2/18.1/155.7/-71.7/-143.8/-0.4），旧 P1/轨迹7/v13 坐标判据全部作废，**重新标零前禁调一切已存点位**。
> 最新权威档案：`sim_scripts/flash_32d8_baseline.md`（§9-11 含根因定论）；交接摘要：`CHECKPOINT_v37.md`。
> 本档仍有效的资产：主控版本-标零约束（原版 8416cf0e 才能标零 / 补丁 9a808cd9 死在 HomeNumdone:2）、HTTP SDO 只读通道、报警码表、碰撞方案、unio FoE 刷写 4 连败记录。'''

assert anchor in s, 'anchor not found'
assert s.count(anchor) == 1, 'anchor not unique'
s = s.replace(anchor, anchor + banner, 1)
io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('banner inserted, new chars =', len(s))
