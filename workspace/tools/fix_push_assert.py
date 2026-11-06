"""修 push_p2p_macro.py 的断言（v15.10 起禁直发名单回到 (9,)）。"""
import io
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
P = r'D:\mydata\glm-workplace\tools\push_p2p_macro.py'
s = io.open(P, encoding='utf-8').read()
old_block = """                  ('MOVL_DIRECT_BLOCK_POINTS = (8, 9)',
                   any(l.strip().startswith('MOVL_DIRECT_BLOCK_POINTS = (8, 9)')
                       for l in text.splitlines())),"""
new_block = """                  ('MOVL_DIRECT_BLOCK_POINTS = (9,)',
                   any(l.strip().startswith('MOVL_DIRECT_BLOCK_POINTS = (9,)')
                       for l in text.splitlines())),"""
if old_block in s:
    s = s.replace(old_block, new_block)
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('  断言已改回 (9,) ✓')
else:
    print('  没找到待替换的断言块，请人工检查')
    for i, l in enumerate(s.splitlines(), 1):
        if 'BLOCK_POINTS' in l:
            print('    L%d: %s' % (i, l))
