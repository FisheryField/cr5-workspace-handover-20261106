"""zf_cdiff.py - normalized diff of two Ghidra decompilation dumps.

Normalizes:
  * FUN_xxxxxxxx / DAT_xxxxxxxx / LAB_xxxxxxxx  -> FUN_X / DAT_X / LAB_X
  * register names rN -> R (keeps statement structure comparable)
  * local variable names  iVarN / uVarN / pcVarN / puVarN / cVarN / sVarN -> V
  * global-RAM and flash absolute addresses -> ADDR
  * byte offsets kept AS IS (they carry the semantics)

usage: python tools/zf_cdiff.py <a.txt> <b.txt> [--ctx N]
"""
import re, sys, difflib


def load(path):
    txt = open(path, encoding='utf-8', errors='replace').read()
    # split into per-function blocks on the '## ' header lines
    blocks = {}
    cur = None
    for line in txt.splitlines():
        m = re.match(r'^## (\S+)', line)
        if m:
            cur = m.group(1)
            blocks[cur] = []
            continue
        if cur:
            blocks[cur].append(line)
    return blocks


def norm_line(s):
    s = s.strip()
    if not s:
        return ''
    s = re.sub(r'\b(?:FUN|DAT|LAB|UNK)_[0-9a-fA-F]{6,8}\b', 'SYM', s)
    s = re.sub(r'\b0x0?80[0-9a-fA-F]{5}\b', 'ADDR', s)
    s = re.sub(r'\b(?:iVar|uVar|pcVar|puVar|ppuVar|cVar|sVar|bVar|local_|auStack_|uStack_|'
               r'iStack_|cStack_|pStack_|fStack_|dStack_|abStack_)[0-9a-fA-F]*', 'V', s)
    s = re.sub(r'\b(?:in_|unaff_|extraout_)[A-Za-z0-9_]+', 'V', s)
    s = re.sub(r'\b(?:r|s|d|q|sl|sb|fp|ip|lr|pc)[0-9]{1,2}\b', 'REG', s)
    s = re.sub(r'\b(?:R|S|D|Q)[0-9]{1,2}\b', 'REG', s)
    s = re.sub(r'\(code \*\)', '(code*)', s)
    s = re.sub(r'\s+', ' ', s)
    return s


def main():
    a, b = load(sys.argv[1]), load(sys.argv[2])
    ctx = 2
    if '--ctx' in sys.argv:
        ctx = int(sys.argv[sys.argv.index('--ctx') + 1])
    print('A functions: %s' % list(a))
    print('B functions: %s' % list(b))
    ka, kb = list(a), list(b)
    for k in range(min(len(ka), len(kb))):
        A = [norm_line(x) for x in a[ka[k]]]
        B = [norm_line(x) for x in b[kb[k]]]
        A = [x for x in A if x]
        B = [x for x in B if x]
        print()
        print('#' * 90)
        print('# BLOCK %d : A=%s  B=%s' % (k, ka[k], kb[k]))
        print('#' * 90)
        same = sum(1 for x in A if x in B)
        print('# A lines=%d  B lines=%d  A-lines-also-in-B=%d (%.1f%%)'
              % (len(A), len(B), same, 100.0 * same / max(1, len(A))))
        for line in difflib.unified_diff(A, B, 'A', 'B', lineterm='', n=ctx):
            print(line)


if __name__ == '__main__':
    main()
