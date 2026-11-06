// zf_scan.java - whole-program scanners on the servo firmware.
//
// modes (first arg):
//   funcs    list every function (entry, name, size)
//   callers  <addr>[,<addr>...]   -> who calls these (function + call site)
//   field    <offset>             -> every instruction touching [reg + offset]
//                                    with the function it lives in
//   decomp   <addr>[,<addr>...]   -> decompile those functions
//   xref     <addr>[,<addr>...]   -> all references (code/data) to those addrs
//
// @category servo

import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.List;

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.scalar.Scalar;
import ghidra.program.model.symbol.Reference;

public class zf_scan extends GhidraScript {

    private List<String> buf = new ArrayList<String>();

    private void emit(String s) {
        println(s);
        buf.add(s);
    }

    private long parseHex(String s) {
        String t = s.trim();
        if (t.toLowerCase().startsWith("0x")) {
            t = t.substring(2);
        }
        return Long.parseLong(t, 16);
    }

    private String fname(Address a) {
        Function f = getFunctionContaining(a);
        return f == null ? "(nofunc)" : (f.getName() + "@" + f.getEntryPoint());
    }

    private void funcs() {
        FunctionIterator it = currentProgram.getFunctionManager().getFunctions(true);
        int n = 0;
        while (it.hasNext()) {
            Function f = it.next();
            long sz = f.getBody().getNumAddresses();
            emit(String.format("%s  %-28s size=0x%x", f.getEntryPoint(), f.getName(), sz));
            n++;
        }
        emit("# total functions = " + n);
    }

    private void callers(List<String> addrs) {
        for (String one : addrs) {
            long v = parseHex(one);
            Address a = toAddr(v);
            emit("### callers of 0x" + Long.toHexString(v));
            Reference[] refs = getReferencesTo(a);
            if (refs.length == 0) {
                emit("    (no references)");
            }
            for (Reference r : refs) {
                Address from = r.getFromAddress();
                emit(String.format("    from %s  %s   [%s]  %s", from, fname(from),
                        r.getReferenceType(),
                        getInstructionAt(from) == null ? "" : getInstructionAt(from).toString()));
            }
            // fallback: brute-force every bl/b instructions for this target
            emit("    -- brute-force bl/b scan --");
            FunctionIterator fit = currentProgram.getFunctionManager().getFunctions(true);
            while (fit.hasNext()) {
                Function f = fit.next();
                InstructionIterator it = currentProgram.getListing().getInstructions(f.getBody(), true);
                while (it.hasNext()) {
                    Instruction ins = it.next();
                    String mn = ins.getMnemonicString();
                    if (!(mn.equals("bl") || mn.equals("b") || mn.equals("blx") || mn.equals("b.w"))) {
                        continue;
                    }
                    for (Object o : ins.getOpObjects(0)) {
                        if (o instanceof Scalar) {
                            long t = ((Scalar) o).getUnsignedValue() & ~1L;
                            if (t == (v & ~1L)) {
                                emit(String.format("    %s  %-30s  in %s", ins.getAddress(),
                                        ins.toString(), fname(ins.getAddress())));
                            }
                        }
                    }
                }
            }
            emit("");
        }
    }

    private void field(long off) {
        emit(String.format("### every instruction with a memory operand [reg + 0x%x]", off));
        FunctionIterator fit = currentProgram.getFunctionManager().getFunctions(true);
        while (fit.hasNext()) {
            Function f = fit.next();
            InstructionIterator it = currentProgram.getListing().getInstructions(f.getBody(), true);
            while (it.hasNext()) {
                Instruction ins = it.next();
                for (int opi = 0; opi < ins.getNumOperands(); opi++) {
                    Object[] objs = ins.getOpObjects(opi);
                    for (Object o : objs) {
                        if (o instanceof Scalar) {
                            Scalar s = (Scalar) o;
                            if (s.getUnsignedValue() == off) {
                                emit(String.format("    %s  %-34s  %s", ins.getAddress(),
                                        ins.toString(), fname(ins.getAddress())));
                                break;
                            }
                        }
                    }
                }
            }
        }
        emit("");
    }

    private void xref(List<String> addrs) {
        for (String one : addrs) {
            long v = parseHex(one);
            Address a = toAddr(v);
            emit("### refs to 0x" + Long.toHexString(v));
            for (Reference r : getReferencesTo(a)) {
                Address from = r.getFromAddress();
                emit(String.format("    %s  %s  [%s]  %s", from, fname(from),
                        r.getReferenceType(),
                        getInstructionAt(from) == null ? "" : getInstructionAt(from).toString()));
            }
            emit("");
        }
    }

    private void decomp(DecompInterface d, List<String> addrs) throws Exception {
        for (String one : addrs) {
            long v = parseHex(one);
            Address a = toAddr(v);
            Function f = getFunctionContaining(a);
            if (f == null) {
                if (getInstructionAt(a) == null) {
                    disassemble(a);
                }
                f = createFunction(a, null);
            }
            emit("");
            emit("================================================================================");
            emit(String.format("## %s -> %s", a, f == null ? "?" : f.getName() + " @" + f.getEntryPoint()));
            emit("================================================================================");
            if (f == null) {
                emit("   (no function)");
                continue;
            }
            DecompileResults res = d.decompileFunction(f, 120, monitor);
            if (res == null || !res.decompileCompleted()) {
                emit("   decompile failed: " + (res == null ? "null" : res.getErrorMessage()));
            } else {
                emit(res.getDecompiledFunction().getC());
            }
        }
    }

    private void ptrinit(long lo, long hi) {
        emit(String.format("### stores whose stored value or base points into 0x%x..0x%x", lo, hi));
        FunctionIterator fit = currentProgram.getFunctionManager().getFunctions(true);
        while (fit.hasNext()) {
            Function f = fit.next();
            InstructionIterator it = currentProgram.getListing().getInstructions(f.getBody(), true);
            while (it.hasNext()) {
                Instruction ins = it.next();
                if (!ins.getMnemonicString().startsWith("str")) {
                    continue;
                }
                for (int opi = 0; opi < ins.getNumOperands(); opi++) {
                    for (Object o : ins.getOpObjects(opi)) {
                        if (o instanceof Scalar) {
                            long v = ((Scalar) o).getUnsignedValue();
                            if (v >= lo && v <= hi) {
                                emit(String.format("    %s  %-34s  %s", ins.getAddress(),
                                        ins.toString(), fname(ins.getAddress())));
                            }
                        }
                    }
                }
            }
        }
        emit("");
    }

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        String outPath = System.getenv("ZF_OUT");
        List<String> rest = new ArrayList<String>();
        String mode = null;
        for (String a : args) {
            if (a.startsWith("out=")) {
                outPath = a.substring(4);
            } else if (mode == null) {
                mode = a;
            } else {
                for (String p : a.split(",")) {
                    if (!p.isEmpty()) {
                        rest.add(p);
                    }
                }
            }
        }
        emit("# program=" + currentProgram.getName() + "  mode=" + mode);
        DecompInterface d = new DecompInterface();
        d.openProgram(currentProgram);
        if ("funcs".equals(mode)) {
            funcs();
        } else if ("callers".equals(mode)) {
            callers(rest);
        } else if ("field".equals(mode)) {
            field(parseHex(rest.get(0)));
        } else if ("xref".equals(mode)) {
            xref(rest);
        } else if ("decomp".equals(mode)) {
            decomp(d, rest);
        } else if ("ptrinit".equals(mode)) {
            ptrinit(parseHex(rest.get(0)), parseHex(rest.get(1)));
        } else {
            emit("unknown mode " + mode);
        }
        if (outPath != null) {
            PrintWriter pw = new PrintWriter(outPath, "UTF-8");
            for (String s : buf) {
                pw.println(s);
            }
            pw.close();
            println("[zf_scan] wrote " + outPath + " (" + buf.size() + " lines)");
        }
    }
}
