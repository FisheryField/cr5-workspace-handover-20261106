// zf_map.java - structural map + targeted decompilation of the servo firmware.
//
// 1. search all memory for anchor constants (magics, flash keys, flash regs);
//    for each hit report which FUNCTION references it (via Ghidra's reference
//    table, which handles literal pools correctly) -- not just which function
//    physically contains the literal bytes.
// 2. decompile a fixed list of addresses for the NV subsystem.
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
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.mem.MemoryBlock;
import ghidra.program.model.symbol.Reference;

public class zf_map extends GhidraScript {

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

    private Function forceFunction(Address addr) throws Exception {
        Function f = getFunctionContaining(addr);
        if (f != null) {
            return f;
        }
        if (getInstructionAt(addr) == null) {
            disassemble(addr);
        }
        return createFunction(addr, null);
    }

    private String refWhere(Address hit) {
        StringBuilder sb = new StringBuilder();
        Reference[] refs = getReferencesTo(hit);
        int n = 0;
        for (Reference r : refs) {
            Address from = r.getFromAddress();
            Function f = getFunctionContaining(from);
            sb.append("      refFrom ").append(from).append("  ")
              .append(f == null ? "(no func)" : f.getName() + "@" + f.getEntryPoint())
              .append("\n");
            n++;
            if (n >= 8) {
                break;
            }
        }
        if (n == 0) {
            sb.append("      (no references recorded)\n");
        }
        return sb.toString();
    }

    private void searchConst(long v, String label) {
        Memory mem = currentProgram.getMemory();
        byte[] pat = new byte[4];
        pat[0] = (byte) (v & 0xff);
        pat[1] = (byte) ((v >> 8) & 0xff);
        pat[2] = (byte) ((v >> 16) & 0xff);
        pat[3] = (byte) ((v >> 24) & 0xff);
        emit(String.format("### const 0x%08x  (%s)", v, label));
        for (MemoryBlock b : mem.getBlocks()) {
            if (!b.isInitialized()) {
                continue;
            }
            Address a = b.getStart();
            int found = 0;
            while (a != null && a.compareTo(b.getEnd()) < 0 && found < 24) {
                Address hit = mem.findBytes(a, b.getEnd(), pat, null, true, monitor);
                if (hit == null) {
                    break;
                }
                emit(String.format("    hit %s  [%s]", hit, b.getName()));
                String rw = refWhere(hit);
                for (String line : rw.split("\n")) {
                    emit(line);
                }
                found++;
                a = hit.add(1);
            }
        }
        emit("");
    }

    private void dumpFunc(String what, Address addr, DecompInterface decomp, int maxIns)
            throws Exception {
        Function f = forceFunction(addr);
        emit("");
        emit("================================================================================");
        emit(String.format("## %s  addr=%s -> %s entry=%s", what, addr,
                f == null ? "?" : f.getName(),
                f == null ? "-" : f.getEntryPoint().toString()));
        emit("================================================================================");
        if (f == null) {
            emit("   (could not create function)");
            return;
        }
        DecompileResults res = decomp.decompileFunction(f, 120, monitor);
        if (res == null || !res.decompileCompleted()) {
            emit("   decompile failed: " + (res == null ? "null" : res.getErrorMessage()));
        } else {
            emit(res.getDecompiledFunction().getC());
        }
        emit("---- listing ----");
        InstructionIterator it = currentProgram.getListing().getInstructions(f.getBody(), true);
        int n = 0;
        while (it.hasNext() && n < maxIns) {
            Instruction ins = it.next();
            emit("   " + ins.getAddress() + "  " + ins.toString());
            n++;
        }
        if (n >= maxIns) {
            emit("   ... (truncated)");
        }
    }

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        List<String> addrs = new ArrayList<String>();
        String outPath = System.getenv("ZF_OUT");
        boolean mapOnly = false;
        for (String a : args) {
            if (a.startsWith("out=")) {
                outPath = a.substring(4);
            } else if (a.equals("maponly")) {
                mapOnly = true;
            } else if (a.startsWith("-")) {
                continue;
            } else {
                addrs.add(a);
            }
        }

        emit("# program=" + currentProgram.getName() + "  imageBase="
                + currentProgram.getImageBase() + "  lang="
                + currentProgram.getLanguageID());

        DecompInterface decomp = new DecompInterface();
        decomp.openProgram(currentProgram);

        searchConst(0xBE6D4A8BL, "flash log record magic");
        searchConst(0xA1B2C3D4L, "param block magic");
        searchConst(0x45670123L, "FLASH_KEY1");
        searchConst(0xCDEF89ABL, "FLASH_KEY2");
        searchConst(0x40023C00L, "FLASH reg base");
        searchConst(0x0800C000L, "log area / param save area start");
        searchConst(0x08080000L, "log high-water mark");

        if (!mapOnly) {
            for (String one : addrs) {
                long v = parseHex(one);
                Address a = toAddr(v);
                dumpFunc("requested " + one, a, decomp, 600);
            }
        }

        if (outPath != null) {
            PrintWriter pw = new PrintWriter(outPath, "UTF-8");
            for (String s : buf) {
                pw.println(s);
            }
            pw.close();
            println("[zf_map] wrote " + outPath + " (" + buf.size() + " lines)");
        }
    }
}
