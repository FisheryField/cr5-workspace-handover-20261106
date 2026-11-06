#!/usr/bin/env python3
"""zgh.py -- run the Ghidra z_gh.java script headless against one of the two
servo programs and print only the script's own output.

usage:
  python tools\\zgh.py a mem 0x08011800 32 decomp 0x0801175a
  python tools\\zgh.py b decomp 0x0801175a
  python tools\\zgh.py both imm 0x4e20 5
"""
import os
import subprocess
import sys

JAVA_HOME = r'D:\software\disassembly\jdk21\jdk-21.0.12.1+1'
HEADLESS = r'D:\software\disassembly\ghidra\ghidra_12.1.4_PUBLIC\support\analyzeHeadless.bat'
SCRIPTS = r'D:\mydata\workspace\.zgh'
# The Ghidra projects were imported from an ELF whose .text is labelled
# 0x08000000 while the payload really lives at 0x08010000 (LOAD_ADDR_VERDICT.txt).
# Every address Ghidra prints is therefore 0x10000 LOW.  BIAS converts a
# Ghidra-side address into a TRUE flash address.
BIAS = 0x10000
PROJ = {
    'a': (r'D:\software\disassembly\ghproj_servo_a', 'servo328d8', 'v328d8.elf'),
    'b': (r'D:\software\disassembly\ghproj_servo_b', 'servo3150', 'v3150.elf'),
}
TAGNAME = {'a': 'D8', 'b': '3150'}


def _once(which, cmds):
    loc, proj, prg = PROJ[which]
    env = dict(os.environ)
    env['JAVA_HOME'] = JAVA_HOME
    # shift every address argument into the real flash space, and let the script
    # shift them back down before touching the program.
    shifted = []
    for c in cmds:
        try:
            v = int(c, 0)
            if c.lower().startswith('0x') and v >= 0x08010100:
                shifted.append(hex(v - BIAS))
                continue
        except ValueError:
            pass
        shifted.append(c)
    argv = [HEADLESS, loc, proj, '-process', prg, '-noanalysis',
            '-scriptPath', SCRIPTS, '-postScript', 'z_gh.java'] + shifted
    p = subprocess.run(argv, capture_output=True, env=env)
    out = (p.stdout or b'').decode('utf-8', 'replace') + (p.stderr or b'').decode('utf-8', 'replace')
    return out


ADDR_RE = None


def _retag(text):
    """Add BIAS to every flash-space address token (0x0801xxxx..) in the output,
    so reports carry true flash addresses."""
    import re
    global ADDR_RE
    if ADDR_RE is None:
        ADDR_RE = re.compile(r'\b(080[1-6][0-9a-f]{4})\b', re.I)

    def sub(m):
        v = int(m.group(1), 16) + BIAS
        return '%08x' % v

    return ADDR_RE.sub(sub, text)


def run(which, cmds, retries=4):
    import time
    out = ''
    for k in range(retries):
        out = _once(which, cmds)
        if 'LockException' not in out and 'Unable to lock project' not in out:
            break
        time.sleep(4 + 4 * k)
    lines = []
    for ln in out.splitlines():
        i = ln.find('z_gh.java> ')
        if i >= 0:
            lines.append(_retag(ln[i + len('z_gh.java> '):]))
        elif 'ERROR' in ln and ('z_gh' in ln or 'LockException' in ln or 'Abort' in ln):
            lines.append('[ghidra] ' + ln.strip())
    return '\n'.join(lines), out


def main(argv):
    which = argv[0]
    cmds = argv[1:]
    if which == 'both':
        for w in ('a', 'b'):
            print('#' * 70)
            print('### %s' % TAGNAME[w])
            print('#' * 70)
            txt, _ = run(w, cmds)
            print(txt)
        return 0
    txt, raw = run(which, cmds)
    print(txt)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
