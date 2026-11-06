"""zf_decomp_all.py - drive Ghidra headless over both programs for a fixed list
of addresses (the persistence / NV subsystem), writing one text file per image.
"""
import subprocess, os, sys

GH = r'D:\software\disassembly\ghidra\ghidra_12.1.4_PUBLIC\support\analyzeHeadless.bat'
JAVA = r'D:\software\disassembly\jdk21\jdk-21.0.12.1+1'
WS = r'D:\mydata\workspace'
TOOLS = os.path.join(WS, 'tools')
OUT = os.path.join(WS, 'tmp_gh')

JOBS = [
    ('D:\\software\\disassembly\\ghproj_servo_a', 'servo328d8', 'v328d8.elf', 'd8', [
        0x08011708,   # param persistence routine (magic A1B2C3D4)  [capstone guess]
        0x080117D0,   # flash log append (magic BE6D4A8B)          [capstone guess]
        0x080145A8,   # persistence API (caller of param persist)
        0x0801449C,   # flash unlock
        0x08014360,   # flash program
        0x08014C3C,   # caller of flash_prog
        0x08019BF8,
        0x08019C40,
    ]),
    ('D:\\software\\disassembly\\ghproj_servo_b', 'servo3150', 'v3150.elf', 'b', [
        0x08011748,
        0x08011810,
        0x0801420C,
        0x08014100,
        0x08013FC4,
        0x080148A0,
        0x080195A0,
        0x080195E8,
    ]),
]

def run(projdir, proj, prog, tag, addrs):
    env = dict(os.environ)
    env['JAVA_HOME'] = JAVA
    abspath = os.path.join(WS, 'tmp_gh', 'decomp_%s.txt' % tag)
    env['ZF_OUT'] = abspath
    cmd = [GH, projdir, proj, '-process', prog, '-noanalysis',
           '-scriptPath', TOOLS, '-postScript', 'zf_map.java']
    cmd += ['0x%08X' % a for a in addrs]
    if os.environ.get('ZF_MAPONLY'):
        cmd.append('maponly')
    print('RUN', tag, abspath)
    p = subprocess.run(cmd, env=env, cwd=WS, input='n\n', capture_output=True,
                       text=True, errors='replace')
    print('   rc=%d' % p.returncode)
    if p.returncode != 0:
        print(p.stdout[-3000:])
    return abspath

if __name__ == '__main__':
    for j in JOBS:
        run(*j)
