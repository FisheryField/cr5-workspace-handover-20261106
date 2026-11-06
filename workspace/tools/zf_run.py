"""zf_run.py - run zf_fn.java on a program for a list of addresses."""
import os, subprocess, sys

GH = r'D:\software\disassembly\ghidra\ghidra_12.1.4_PUBLIC\support\analyzeHeadless.bat'
JAVA = r'D:\software\disassembly\jdk21\jdk-21.0.12.1+1'
WS = r'D:\mydata\workspace'
TOOLS = os.path.join(WS, 'tools')
PROJ = {
    'a': (r'D:\software\disassembly\ghproj_servo_a', 'servo328d8', 'v328d8.elf', 'd8'),
    'b': (r'D:\software\disassembly\ghproj_servo_b', 'servo3150', 'v3150.elf', 'b'),
}


def run(projkey, addrs, tag):
    projdir, proj, prog, ptag = PROJ[projkey]
    out = os.path.join(WS, 'tmp_gh', 'fn_%s_%s.txt' % (ptag, tag))
    env = dict(os.environ)
    env['JAVA_HOME'] = JAVA
    env['ZF_OUT'] = out
    cmd = [GH, projdir, proj, '-process', prog, '-noanalysis',
           '-scriptPath', TOOLS, '-postScript', 'zf_fn.java']
    cmd += ['%08X' % a for a in addrs]
    p = subprocess.run(cmd, env=env, cwd=WS, input='n\n', capture_output=True,
                       text=True, errors='replace')
    open(os.path.join(WS, 'tmp_gh', 'fn_%s_%s.log' % (ptag, tag)), 'w',
         encoding='utf-8', errors='replace').write(p.stdout)
    print('rc=%d out=%s' % (p.returncode, out))
    return out


if __name__ == '__main__':
    key = sys.argv[1]
    tag = sys.argv[2]
    addrs = [int(x, 16) if x.lower().startswith('0x') else int(x, 16)
             for x in sys.argv[3:]]
    run(key, addrs, tag)
