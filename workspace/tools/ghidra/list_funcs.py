# Ghidra headless: 列出关心的函数
from ghidra.program.model.symbol import SourceType
prog = getCurrentProgram()
print('IMAGE BASE = %s' % prog.getImageBase())
fm = prog.getFunctionManager()
allf = list(fm.getFunctions(True))
print('FUNCTION COUNT = %d' % len(allf))
KW = ['parseAndReqSetServoParams','parseAndReqGetServoParams','modifyServoParams','readServoParams',
      'readSDO','writeSDO','exitSDOWRThd','getAndPackServoParams','createSDORWThd','readSDOthd','writeSDOthd']
for f in allf:
    n = f.getName()
    for k in KW:
        if k in n:
            print('  %-70s @ %s  size=%d' % (n, f.getEntryPoint(), f.getBody().getNumAddresses()))
            break