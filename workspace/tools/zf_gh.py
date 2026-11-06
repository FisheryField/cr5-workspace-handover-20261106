"""zf_gh.py - run a Ghidra headless scan on the servo firmware projects.

usage:
  python tools/zf_gh.py a field 0x230
  python tools/zf_gh.py a callers 0x08001708,0x080045A8
  python tools/zf_gh.py a decomp 0x08001708,0x080017D0
  python tools/zf_gh.py a funcs

'ghidra address' = canonical(app) address - 0x10000.
"""
import os, subprocess, sys

GH = r'D:\software\disassembly\ghidra\ghidra_12.1.4_PUBLIC\support\analyzeHeadless.bat'
JAVA = r'D:\software\disassembly\jdk21\jdk-21.0.12.1+1'
WS = r'D:\mydata\workspace'
TOOLS = os.path.join(WS, 'tools')

PROJ = {
    'a': (r'D:\software\disassembly\ghproj_servo_a', 'servo328d8', 'v328d8.elf', 'd8'),
    'b': (r'D:\software\disassembly\ghproj_servo_b', 'servo3150', 'v3150.elf', 'b'),
}


def norm_addr(s):
    """Return the address as BARE HEX DIGITS (no 0x prefix).

    cmd.exe's batch parser drops a leading `0x` from arguments, so the token
    must not carry one; Java's parseHex reads bare hex digits directly.
    """
    t = s.strip()
    if t.lower().startswith('0x'):
        v = int(t[2:], 16)
    elif len(t) >= 6 and all(c in '0123456789abcdefABCDEF' for c in t):
        v = int(t, 16)
    else:
        v = int(t)
    return '%08X' % v


def normalize_args(args):
    if args is None:
        return None
    parts = [p for p in args.split(',') if p]
    if len(parts) == 1:
        return norm_addr(parts[0])
    return ','.join(norm_addr(p) for p in parts)


def run(projkey, mode, args, tag=None, create=True):
    projdir, proj, prog, ptag = PROJ[projkey]
    tag = tag or ('%s_%s' % (ptag, mode))
    out = os.path.join(WS, 'tmp_gh', 'scan_%s.txt' % tag)
    env = dict(os.environ)
    env['JAVA_HOME'] = JAVA
    env['ZF_OUT'] = out
    cmd = [GH, projdir, proj]
    if not create:
        cmd += ['-process', prog, '-noanalysis']
    else:
        cmd += ['-process', prog, '-noanalysis']
    cmd += ['-scriptPath', TOOLS, '-postScript', 'zf_scan.java', mode]
    if args:
        cmd.append(normalize_args(args))
    p = subprocess.run(cmd, env=env, cwd=WS, input='n\n', capture_output=True,
                       text=True, errors='replace')
    log = os.path.join(WS, 'tmp_gh', 'scan_%s.log' % tag)
    open(log, 'w', encoding='utf-8', errors='replace').write(p.stdout)
    print('rc=%d  out=%s' % (p.returncode, out))
    if p.returncode != 0:
        for line in p.stdout.splitlines():
            if 'ERROR' in line or 'Exception' in line:
                print('  ' + line)
    return out


if __name__ == '__main__':
    projkey = sys.argv[1]
    mode = sys.argv[2]
    args = sys.argv[3] if len(sys.argv) > 3 else None
    run(projkey, mode, args)
