// z_inspect.java -- layout + search + decompile harness (2026-09-26 zero-mechanism round)
//@category ZERO
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.*;
import ghidra.program.model.mem.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;
import ghidra.app.decompiler.*;
import ghidra.program.model.pcode.*;
import ghidra.program.model.scalar.Scalar;
import java.math.BigInteger;
import java.util.*;

public class z_inspect extends GhidraScript {

    DecompInterface dec;

    DecompInterface decomp() {
        if (dec == null) {
            dec = new DecompInterface();
            DecompileOptions o = new DecompileOptions();
            dec.setOptions(o);
            dec.openProgram(currentProgram);
        }
        return dec;
    }

    void dumpBlocks() {
        println("### MEMORY BLOCKS of " + currentProgram.getName());
        for (MemoryBlock b : currentProgram.getMemory().getBlocks()) {
            println(String.format("  %-16s %s .. %s  size=%d  r=%b w=%b x=%b init=%b",
                b.getName(), b.getStart(), b.getEnd(), b.getSize(),
                b.isRead(), b.isWrite(), b.isExecute(), b.isInitialized()));
        }
    }

    byte[] hexToBytes(String s) {
        s = s.replace(" ", "");
        byte[] out = new byte[s.length() / 2];
        for (int i = 0; i < out.length; i++)
            out[i] = (byte) Integer.parseInt(s.substring(2 * i, 2 * i + 2), 16);
        return out;
    }

    void search(String hex) {
        byte[] pat = hexToBytes(hex);
        println("### SEARCH '" + hex + "' (" + pat.length + " B)");
        Address a = currentProgram.getMinAddress();
        int n = 0;
        while (a != null && n < 40) {
            a = currentProgram.getMemory().findBytes(a, pat, null, true, monitor);
            if (a == null) break;
            println("  hit @ " + a);
            n++;
            a = a.add(1);
        }
        println("  total shown=" + n);
    }

    void disasm(long addr, int count) {
        Address a = toAddr(addr);
        println("### DISASM @ " + a + " for " + count);
        for (int i = 0; i < count; i++) {
            Instruction ins = getInstructionAt(a);
            if (ins == null) {
                println("  " + a + "  <no instruction>");
                a = a.add(2);
                continue;
            }
            println(String.format("  %s  %-28s %s", ins.getAddress(),
                bytes(ins), ins.toString()));
            a = ins.getAddress().add(ins.getLength());
        }
    }

    String bytes(Instruction ins) {
        StringBuilder sb = new StringBuilder();
        try {
            byte[] b = ins.getBytes();
            for (byte x : b) sb.append(String.format("%02x ", x));
        } catch (Exception e) { }
        return sb.toString().trim();
    }

    void decompile(long addr) {
        Address a = toAddr(addr);
        Function f = getFunctionAt(a);
        if (f == null) f = getFunctionContaining(a);
        if (f == null) { println("### DECOMP " + a + " : NO FUNCTION"); return; }
        println("### FUNCTION " + f.getName() + " @ " + f.getEntryPoint()
                + " size=" + f.getBody().getNumAddresses());
        DecompileResults r = decomp().decompileFunction(f, 90, monitor);
        if (r == null || !r.decompileCompleted()) {
            println("  decompile failed: " + (r == null ? "null" : r.getErrorMessage()));
            return;
        }
        println(r.getDecompiledFunction().getC());
    }

    void listFuncs(String filter) {
        println("### FUNCTIONS matching '" + filter + "'");
        FunctionManager fm = currentProgram.getFunctionManager();
        int n = 0;
        for (Function f : fm.getFunctions(true)) {
            if (f.getName().toLowerCase().contains(filter.toLowerCase())) {
                println("  " + f.getEntryPoint() + "  " + f.getName());
                if (++n > 200) break;
            }
        }
        println("  count=" + n);
    }

    /** every memory access whose displacement equals one of the given values */
    void dispScan(String vals, int maxShow) {
        String[] parts = vals.split(",");
        Set<Long> want = new HashSet<>();
        for (String p : parts) want.add(Long.decode(p.trim()));
        println("### DISPLACEMENT SCAN for " + want);
        Listing lst = currentProgram.getListing();
        int[] shown = new int[parts.length];
        long total = 0;
        for (Instruction ins : lst.getInstructions(true)) {
            for (int op = 0; op < ins.getNumOperands(); op++) {
                for (Object o : ins.getOpObjects(op)) {
                    if (!(o instanceof Scalar)) continue;
                    long v = ((Scalar) o).getUnsignedValue();
                    if (want.contains(v)) {
                        total++;
                        int idx = parts.length;
                        for (int k = 0; k < parts.length; k++)
                            if (Long.decode(parts[k].trim()) == v) idx = k;
                        if (idx < parts.length && shown[idx] < maxShow) {
                            shown[idx]++;
                            println(String.format("  [%s] %s  %s", parts[idx], ins.getAddress(), ins.toString()));
                        }
                    }
                }
            }
        }
        println("  total matching operand scalars = " + total + "  shown=" + Arrays.toString(shown));
    }

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length == 0) { dumpBlocks(); return; }
        for (int i = 0; i < args.length; i++) {
            String c = args[i];
            if (c.equals("blocks")) dumpBlocks();
            else if (c.equals("search")) search(args[++i]);
            else if (c.equals("dis")) disasm(Long.decode(args[++i]), Integer.parseInt(args[++i]));
            else if (c.equals("decomp")) decompile(Long.decode(args[++i]));
            else if (c.equals("funcs")) listFuncs(args[++i]);
            else if (c.equals("disp")) dispScan(args[++i], Integer.parseInt(args[++i]));
            else println("unknown cmd: " + c);
        }
    }
}
