// zf_decomp.java - Ghidra headless script: decompile functions at given addresses
// and dump C-like pseudocode plus the raw listing.
//
// usage:
//   analyzeHeadless <projDir> <projName> -process <progName> -noanalysis \
//       -scriptPath tools -postScript zf_decomp.java 0x08001708 out=<file>
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

public class zf_decomp extends GhidraScript {

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

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        List<String> addrs = new ArrayList<String>();
        String outPath = System.getenv("ZF_OUT");
        for (String a : args) {
            if (a.startsWith("out=")) {
                outPath = a.substring(4);
            } else if (a.startsWith("list=")) {
                for (String p : a.substring(5).split(",")) {
                    addrs.add(p);
                }
            } else if (a.startsWith("-")) {
                continue;
            } else {
                addrs.add(a);
            }
        }

        emit("# program=" + currentProgram.getName() + "  imageBase="
                + currentProgram.getImageBase());

        DecompInterface decomp = new DecompInterface();
        decomp.openProgram(currentProgram);

        for (String one : addrs) {
            Address addr = toAddr(parseHex(one));
            Function f = getFunctionContaining(addr);
            emit("");
            emit("================================================================================");
            emit("## requested " + one + " -> function "
                    + (f == null ? "?" : f.getName()) + " entry="
                    + (f == null ? "-" : f.getEntryPoint().toString()));
            emit("================================================================================");
            if (f == null) {
                emit("   (no function at this address)");
                continue;
            }
            DecompileResults res = decomp.decompileFunction(f, 90, monitor);
            if (res == null || !res.decompileCompleted()) {
                emit("   decompile failed: "
                        + (res == null ? "null" : res.getErrorMessage()));
            } else {
                emit(res.getDecompiledFunction().getC());
            }
            emit("");
            emit("---- listing " + f.getBody().getMinAddress() + " .. "
                    + f.getBody().getMaxAddress() + " ----");
            InstructionIterator it =
                    currentProgram.getListing().getInstructions(f.getBody(), true);
            int n = 0;
            while (it.hasNext() && n < 500) {
                Instruction ins = it.next();
                emit("   " + ins.getAddress() + "  " + ins.toString());
                n++;
            }
            if (n >= 500) {
                emit("   ... (truncated)");
            }
            emit("");
        }

        if (outPath != null) {
            PrintWriter pw = new PrintWriter(outPath, "UTF-8");
            for (String s : buf) {
                pw.println(s);
            }
            pw.close();
            println("[zf_decomp] wrote " + outPath + " (" + buf.size() + " lines)");
        }
    }
}
