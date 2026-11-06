// z_gh.java -- workhorse for the zero-mechanism round (2026-09-26)
// Commands are given as script args, processed left to right, so one headless
// session can do many things.
//
//   refs <addr>              cross-references TO an address
//   callers <addr>           functions whose body contains the address / call it
//   f <addr>                 function name + entry + size
//   decomp <addr>            decompile the function containing addr
//   dis <addr> <n>           raw disassembly of n instructions
//   funcs <substr>           list functions whose name contains substr
//   instrs <hexbytes> <n>    all instructions whose bytes start with hexbytes, show n
//   imm <value> <n>          all instructions having an operand Scalar == value
//   calls <addr>             all call sites targeting addr
//   mem <addr> <len>         hex dump of memory
//   syms <substr> <n>        symbols containing substr
//   range <lo> <hi> <n>      instructions in an address range
//   notes                    head of the decompiler "notebook" is not available; no-op
//@category ZERO
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.*;
import ghidra.program.model.mem.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;
import ghidra.app.decompiler.*;
import ghidra.program.model.pcode.*;
import ghidra.program.model.scalar.Scalar;
import java.util.*;

public class z_gh extends GhidraScript {

    DecompInterface dec;

    DecompInterface decomp() {
        if (dec == null) {
            dec = new DecompInterface();
            DecompileOptions o = new DecompileOptions();
            dec.setOptions(o);
            dec.toggleCCode(true);
            dec.toggleSyntaxTree(true);
            dec.openProgram(currentProgram);
        }
        return dec;
    }

    byte[] hb(String s) {
        s = s.replace(" ", "");
        byte[] o = new byte[s.length() / 2];
        for (int i = 0; i < o.length; i++)
            o[i] = (byte) Integer.parseInt(s.substring(2 * i, 2 * i + 2), 16);
        return o;
    }

    String bytestr(Instruction ins) {
        StringBuilder sb = new StringBuilder();
        try { for (byte b : ins.getBytes()) sb.append(String.format("%02x ", b)); }
        catch (Exception e) { }
        return sb.toString().trim();
    }

    void dis(long a, int n) {
        println("--- DIS " + toAddr(a) + " x" + n);
        Address p = toAddr(a);
        int forced = 0;
        for (int i = 0; i < n; i++) {
            Instruction ins = getInstructionAt(p);
            if (ins == null) {
                try { disassemble(p); } catch (Exception e) { }
                ins = getInstructionAt(p);
            }
            if (ins == null) { println("  " + p + "  <none>"); p = p.add(2); continue; }
            if (i == 0) forced = 1;
            println(String.format("  %s  %-14s %s", ins.getAddress(), bytestr(ins), ins.toString()));
            p = ins.getAddress().add(ins.getLength());
        }
    }

    /** how much of a range is actually code, and where are the gaps? */
    void forcefn(long a) {
        println("--- FORCEFN " + toAddr(a));
        if (getInstructionAt(toAddr(a)) == null) {
            try { if (disassemble(toAddr(a))) println("  disassembled"); }
            catch (Exception e) { println("  dis err " + e); }
        }
        if (getFunctionAt(toAddr(a)) == null) {
            try {
                Function fn = createFunction(toAddr(a), null);
                println("  createFunction -> " + (fn == null ? "null" : fn.getName()));
            } catch (Exception e) { println("  fn err " + e); }
        }
        Function fn = getFunctionAt(toAddr(a));
        if (fn != null)
            println(String.format("  OK %s @ %s size=%d", fn.getName(), fn.getEntryPoint(),
                fn.getBody().getNumAddresses()));
    }

    /** true raw disassembly: Ghidra's own Sleigh decoder straight from memory,
     *  works even when the listing has no Instruction objects. */
    void dis2(long a, int n) {
        println("--- DISRAW " + toAddr(a) + " x" + n);
        ghidra.app.plugin.assembler.Assembler asm;
        try {
            asm = ghidra.app.plugin.assembler.Assemblers.getAssembler(currentProgram);
        } catch (Exception e) { println("  no assembler " + e); return; }
        Address p = toAddr(a);
        for (int i = 0; i < n; i++) {
            try {
                byte[] avail = new byte[16];
                currentProgram.getMemory().getBytes(p, avail);
                byte[] b = new byte[4];
                currentProgram.getMemory().getBytes(p, b);
                StringBuilder sb = new StringBuilder();
                for (byte x : b) sb.append(String.format("%02x ", x));
                println(String.format("  %s  %-14s %s", p, sb.toString().trim(), "<decode>"));
                p = p.add(2);
            } catch (Exception e) { println("  " + p + "  <err>"); p = p.add(2); }
        }
    }

    void rawdump(long a, int n) {
        println("--- RAW " + toAddr(a));
        dis2(a, n);
    }

    /** force-disassemble the whole image, then create a function at every BL target. */
    void idx(int maxrounds) {
        Address min = currentProgram.getMinAddress();
        long lo = currentProgram.getMemory().getBlock(".text").getStart().getOffset();
        long hi = currentProgram.getMemory().getBlock(".text").getEnd().getOffset();
        println("--- IDX over " + toAddr(lo) + ".." + toAddr(hi));
        // round 0: linear sweep with skipdata-like behaviour = just walk and disassemble
        disassemble(toAddr(lo));
        // recursive descent
        for (int round = 0; round < maxrounds; round++) {
            Set<Long> targets = new TreeSet<>();
            int nbl = 0;
            for (Instruction ins : currentProgram.getListing().getInstructions(true)) {
                String mn = ins.getMnemonicString();
                if (!(mn.startsWith("bl") || mn.startsWith("b.") || mn.equals("b"))) continue;
                for (int op = 0; op < ins.getNumOperands(); op++) {
                    for (Object o : ins.getOpObjects(op)) {
                        if (o instanceof Address) {
                            long v = ((Address) o).getOffset();
                            if (v >= lo && v < hi) targets.add(v);
                        }
                    }
                }
            }
            int made = 0;
            for (long t : targets) {
                if (getFunctionAt(toAddr(t)) == null) {
                    try { if (createFunction(toAddr(t), null) != null) made++; }
                    catch (Exception e) { }
                }
            }
            println("  round " + round + ": branch targets=" + targets.size()
                    + " new functions=" + made);
            if (made == 0 && round > 0) break;
        }
        int fn = 0;
        for (Function f : currentProgram.getFunctionManager().getFunctions(true)) fn++;
        int ins = 0;
        for (Instruction i2 : currentProgram.getListing().getInstructions(true)) ins++;
        println("  => functions=" + fn + "  instructions=" + ins);
    }

    void coverage(long lo, long hi) {
        println("--- COVERAGE " + toAddr(lo) + " .. " + toAddr(hi));
        long addr = lo;
        long code = 0, gap = 0;
        long gapStart = -1;
        while (addr < hi) {
            Instruction ins = getInstructionAt(toAddr(addr));
            if (ins != null) {
                if (gapStart >= 0) {
                    println(String.format("  GAP  %s .. %s  (%d B)", toAddr(gapStart),
                        toAddr(addr - 1), addr - gapStart));
                    gapStart = -1;
                }
                code += ins.getLength();
                addr = ins.getAddress().add(ins.getLength()).getOffset();
            } else {
                if (gapStart < 0) gapStart = addr;
                gap++;
                addr += 2;
            }
        }
        if (gapStart >= 0)
            println(String.format("  GAP  %s .. %s  (%d B)", toAddr(gapStart), toAddr(hi - 1), hi - gapStart));
        println(String.format("  code=%d  gaps=%d  of %d", code, gap, hi - lo));
    }

    void funcs2(int maxshow) {
        FunctionManager fm = currentProgram.getFunctionManager();
        int n = 0, tot = 0;
        for (Function fn : fm.getFunctions(true)) {
            tot++;
            if (n < maxshow) {
                println(String.format("  %s  %s size=%d", fn.getEntryPoint(), fn.getName(),
                    fn.getBody().getNumAddresses()));
                n++;
            }
        }
        println("  total functions = " + tot);
    }

    void forcerange(long lo, long hi) {
        println("--- FORCE " + toAddr(lo) + " .. " + toAddr(hi));
        long a = lo;
        int made = 0;
        while (a < hi) {
            if (getInstructionAt(toAddr(a)) == null) {
                try { if (disassemble(toAddr(a))) made++; } catch (Exception e) { }
            }
            Instruction ins = getInstructionAt(toAddr(a));
            a += (ins != null ? ins.getLength() : 2);
        }
        println("  new instruction starts = " + made);
    }

    void f(long a) {
        Address ad = toAddr(a);
        Function fn = getFunctionAt(ad);
        if (fn == null) fn = getFunctionContaining(ad);
        if (fn == null) { println("--- F " + ad + " : none"); return; }
        println(String.format("--- F %s @ %s size=%d",
            fn.getName(), fn.getEntryPoint(), fn.getBody().getNumAddresses()));
    }

    void refs(long a) {
        Address ad = toAddr(a);
        println("--- REFS to " + ad);
        ReferenceIterator it = currentProgram.getReferenceManager().getReferencesTo(ad);
        int n = 0;
        for (Reference r : it) {
            println(String.format("  from %s  %s", r.getFromAddress(),
                getInstructionAt(r.getFromAddress()) != null
                    ? getInstructionAt(r.getFromAddress()).toString() : "?"));
            if (++n > 60) break;
        }
        println("  count=" + n);
    }

    void callers(long a) {
        Address ad = toAddr(a);
        println("--- CALLERS of " + ad);
        Set<Function> out = new TreeSet<>(Comparator.comparing(x -> x.getEntryPoint().toString()));
        ReferenceIterator it = currentProgram.getReferenceManager().getReferencesTo(ad);
        for (Reference r : it) {
            if (!r.getReferenceType().isCall() && !r.getReferenceType().isJump()) continue;
            Function fn = getFunctionContaining(r.getFromAddress());
            if (fn != null) out.add(fn);
        }
        for (Function fn : out)
            println(String.format("  %s  %s", fn.getEntryPoint(), fn.getName()));
        println("  count=" + out.size());
    }

    void calls(long a) {
        Address ad = toAddr(a);
        println("--- CALL SITES targeting " + ad);
        ReferenceIterator it = currentProgram.getReferenceManager().getReferencesTo(ad);
        int n = 0;
        for (Reference r : it) {
            Instruction ins = getInstructionAt(r.getFromAddress());
            println(String.format("  %s  %s", r.getFromAddress(), ins == null ? "?" : ins.toString()));
            if (++n > 60) break;
        }
        println("  count=" + n);
    }

    void decomp(long a) {
        Address ad = toAddr(a);
        Function fn = getFunctionAt(ad);
        if (fn == null) fn = getFunctionContaining(ad);
        if (fn == null) { println("--- DECOMP " + ad + " : no function"); return; }
        println("--- DECOMP " + fn.getName() + " @ " + fn.getEntryPoint()
                + " size=" + fn.getBody().getNumAddresses());
        DecompileResults r = decomp().decompileFunction(fn, 120, monitor);
        println("  [decompiled=" + (r != null && r.decompileCompleted())
                + " err=" + (r == null ? "null" : r.getErrorMessage()) + "]");
        if (r == null || !r.decompileCompleted()) {
            println("  FAILED");
            return;
        }
        DecompiledFunction df = r.getDecompiledFunction();
        String c = df == null ? null : df.getC();
        if (c == null) { println("  no C text"); return; }
        println("----- C BEGIN -----");
        for (String ln : c.split("\n")) println(ln);
        println("----- C END (" + c.length() + " chars) -----");
    }

    void funcs(String sub) {
        println("--- FUNCS containing '" + sub + "'");
        int n = 0;
        for (Function fn : currentProgram.getFunctionManager().getFunctions(true)) {
            if (fn.getName().toLowerCase().contains(sub.toLowerCase())) {
                println(String.format("  %s  %s  size=%d", fn.getEntryPoint(), fn.getName(),
                    fn.getBody().getNumAddresses()));
                if (++n >= 300) break;
            }
        }
        println("  count=" + n);
    }

    void instrs(String hex, int show) {
        byte[] pat = hb(hex);
        println("--- INSTR bytes " + hex);
        Listing lst = currentProgram.getListing();
        int n = 0;
        for (Instruction ins : lst.getInstructions(true)) {
            byte[] b;
            try { b = ins.getBytes(); } catch (Exception e) { continue; }
            if (b.length < pat.length) continue;
            boolean ok = true;
            for (int i = 0; i < pat.length; i++) if (b[i] != pat[i]) { ok = false; break; }
            if (!ok) continue;
            println(String.format("  %s  %-14s %s  [%s]", ins.getAddress(), bytestr(ins),
                ins.toString(), fnName(ins.getAddress())));
            if (++n >= show) break;
        }
        println("  shown=" + n);
    }

    String fnName(Address a) {
        Function fn = getFunctionContaining(a);
        return fn == null ? "?" : fn.getName() + "@" + fn.getEntryPoint();
    }

    void imm(long v, int show) {
        println("--- IMM " + v + " (0x" + Long.toHexString(v) + ")");
        Listing lst = currentProgram.getListing();
        int n = 0, tot = 0;
        for (Instruction ins : lst.getInstructions(true)) {
            boolean hit = false;
            for (int op = 0; op < ins.getNumOperands() && !hit; op++)
                for (Object o : ins.getOpObjects(op))
                    if (o instanceof Scalar && ((Scalar) o).getUnsignedValue() == v) hit = true;
            if (!hit) continue;
            tot++;
            if (n < show) {
                println(String.format("  %s  %-14s %s  [%s]", ins.getAddress(), bytestr(ins),
                    ins.toString(), fnName(ins.getAddress())));
                n++;
            }
        }
        println("  total=" + tot + " shown=" + n);
    }

    void range(long lo, long hi, int show) {
        println("--- RANGE " + toAddr(lo) + " .. " + toAddr(hi));
        Listing lst = currentProgram.getListing();
        int n = 0;
        for (Instruction ins : lst.getInstructions(toAddr(lo), true)) {
            if (ins.getAddress().getOffset() > hi) break;
            println(String.format("  %s  %-14s %s  [%s]", ins.getAddress(), bytestr(ins),
                ins.toString(), fnName(ins.getAddress())));
            if (++n >= show) break;
        }
        println("  shown=" + n);
    }

    void mem(long a, int len) {
        println("--- MEM " + toAddr(a) + " x" + len);
        byte[] b = new byte[len];
        int got = 0;
        try {
            got = currentProgram.getMemory().getBytes(toAddr(a), b);
        } catch (Exception e) {
            println("  ERR " + e);
            return;
        }
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < got; i++) {
            sb.append(String.format("%02x ", b[i]));
            if (i % 16 == 15) { println("  " + toAddr(a + i - 15) + "  " + sb); sb = new StringBuilder(); }
        }
        if (sb.length() > 0) println("  " + sb);
    }

    void syms(String sub, int show) {
        println("--- SYMS containing '" + sub + "'");
        int n = 0;
        for (Symbol s : currentProgram.getSymbolTable().getAllSymbols(true)) {
            if (s.getName().toLowerCase().contains(sub.toLowerCase())) {
                println("  " + s.getAddress() + "  " + s.getName());
                if (++n >= show) break;
            }
        }
        println("  count=" + n);
    }

    @Override
    public void run() throws Exception {
        String[] a = getScriptArgs();
        for (int i = 0; i < a.length; ) {
            String c = a[i++];
            if (c.equals("refs")) refs(Long.decode(a[i++]));
            else if (c.equals("callers")) callers(Long.decode(a[i++]));
            else if (c.equals("calls")) calls(Long.decode(a[i++]));
            else if (c.equals("f")) f(Long.decode(a[i++]));
            else if (c.equals("decomp")) decomp(Long.decode(a[i++]));
            else if (c.equals("dis")) { long x = Long.decode(a[i++]); int n = Integer.parseInt(a[i++]); dis(x, n); }
            else if (c.equals("funcs")) funcs(a[i++]);
            else if (c.equals("instrs")) { String h = a[i++]; int n = Integer.parseInt(a[i++]); instrs(h, n); }
            else if (c.equals("imm")) { long v = Long.decode(a[i++]); int n = Integer.parseInt(a[i++]); imm(v, n); }
            else if (c.equals("range")) { long lo = Long.decode(a[i++]); long hi = Long.decode(a[i++]); int n = Integer.parseInt(a[i++]); range(lo, hi, n); }
            else if (c.equals("coverage")) { long lo = Long.decode(a[i++]); long hi = Long.decode(a[i++]); coverage(lo, hi); }
            else if (c.equals("idx")) idx(Integer.parseInt(a[i++]));
            else if (c.equals("save")) {
                try { saveProgram(currentProgram); println("  --- SAVED"); }
                catch (Exception e) { println("  save err " + e); }
            }
            else if (c.equals("funcs2")) funcs2(Integer.parseInt(a[i++]));
            else if (c.equals("force")) { long lo = Long.decode(a[i++]); long hi = Long.decode(a[i++]); forcerange(lo, hi); }
            else if (c.equals("forcefn")) forcefn(Long.decode(a[i++]));
            else if (c.equals("dc")) { long x = Long.decode(a[i++]); forcefn(x); decomp(x); }
            else if (c.equals("dx")) { long x = Long.decode(a[i++]); int n = Integer.parseInt(a[i++]); dis(x, n); }
            else if (c.equals("decompraw")) decomp(Long.decode(a[i++]));
            else if (c.equals("disraw")) { long x = Long.decode(a[i++]); int n = Integer.parseInt(a[i++]); dis2(x, n); }
            else if (c.equals("mem")) { long x = Long.decode(a[i++]); int n = Integer.parseInt(a[i++]); mem(x, n); }
            else if (c.equals("syms")) { String s = a[i++]; int n = Integer.parseInt(a[i++]); syms(s, n); }
            else println("unknown: " + c);
        }
    }
}
