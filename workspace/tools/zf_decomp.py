# -*- coding: utf-8 -*-
# zf_decomp.py - Ghidra headless script: decompile functions at given addresses
# and dump C-like pseudocode plus the raw listing.
#
# usage:
#   analyzeHeadless <projDir> <projName> -process <progName> -noanalysis \
#       -scriptPath tools -postScript zf_decomp.py 0x08001708 0x080045A8
#
# extra args:
#   out=<file>   write output there as well
#   list=<addr>,<addr>,...   additional addresses
# @category servo
import os
import re

from ghidra.app.decompiler import DecompInterface
from ghidra.util.task import ConsoleTaskMonitor

args = list(getScriptArgs())
addrs = []
outpath = None
for a in args:
    if a.startswith('out='):
        outpath = a[4:]
    elif a.startswith('list='):
        addrs.extend(a[5:].split(','))
    elif a.startswith('-'):
        continue
    else:
        addrs.append(a)

buf = []


def emit(s):
    print(s)
    buf.append(s)


def toaddr(x):
    if isinstance(x, (int, long)):
        return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(x)
    s = x.strip()
    v = int(s, 16) if s.lower().startswith('0x') else int(s, 16)
    return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(v)


def funcname(f):
    if f is None:
        return '?'
    return f.getName()


fm = currentProgram.getFunctionManager()
decomp = DecompInterface()
decomp.openProgram(currentProgram)
mon = ConsoleTaskMonitor()

emit('# program=%s  imageBase=%s' % (currentProgram.getName(),
                                     currentProgram.getImageBase()))
for a in addrs:
    if ',' in a:
        parts = a.split(',')
    else:
        parts = [a]
    for one in parts:
        addr = toaddr(one)
        f = fm.getFunctionContaining(addr)
        emit('')
        emit('=' * 100)
        emit('## requested 0x%s -> function %s  entry=%s' %
             (one.replace('0x', ''), funcname(f), f.getEntryPoint() if f else '-'))
        emit('=' * 100)
        if f is None:
            emit('   (no function at this address)')
            continue
        res = decomp.decompileFunction(f, 60, mon)
        if res is None or not res.decompileCompleted():
            emit('   decompile failed: %s' % (res.getErrorMessage() if res else 'None'))
        else:
            emit(res.getDecompiledFunction().getC())
        # raw listing
        body = f.getBody()
        emit('')
        emit('---- listing %s .. %s ----' % (body.getMinAddress(), body.getMaxAddress()))
        it = currentProgram.getListing().getInstructions(body, True)
        n = 0
        for ins in it:
            emit('   %s  %s' % (ins.getAddress(), ins))
            n += 1
            if n > 400:
                emit('   ... (truncated)')
                break
        emit('')

if outpath:
    fh = open(outpath, 'w')
    fh.write('\n'.join(buf))
    fh.close()
    print('[zf_decomp] wrote %s (%d lines)' % (outpath, len(buf)))
