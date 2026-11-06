"""Preserve historical notes while updating the tool-fix version labels."""
from pathlib import Path
root = Path(__file__).resolve().parents[1]
path = root / 'sim_scripts' / 'TCP真实运动_P2P版.py'
text = path.read_text(encoding='utf-8')
original = (root / 'sim_scripts' / 'TCP真实运动_P2P版_v14w40_before_toolfix_20261027.py.bak').read_text(encoding='utf-8')
old_version_line = next(line for line in original.splitlines() if line.startswith('LOG_VERSION ='))
history = old_version_line.split('  # ', 1)[1]
text = text.replace('# v14w40 基准：工具126；后续场景已调整，以当前站内物件为准，历史注释不作实时坐标。',
                    '# 历史版本记录（场景坐标并非实时状态）：' + history)
text = text.replace('P2P v14w40', 'P2P v14w41').replace('【v14w40】', '【v14w41】')
path.write_text(text, encoding='utf-8')
