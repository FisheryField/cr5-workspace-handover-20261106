// zf_fn.java - decompile + full listing for a function, byte-addressable compare.
// args: <addr> [<addr>...]
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

public class zf_fn extends GhidraScript {

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
        String outPath = System.getenv("ZF_OUT");
        DecompInterface d = new DecompInterface();
        d.openProgram(currentProgram);
        emit("# program=" + currentProgram.getName());
        for (String one : args) {
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
            emit("================================");
            emit("## " + a + " -> " + (f == null ? "?" : f.getName() + " @" + f.getEntryPoint()));
            emit("================================");
            if (f != null) {
                DecompileResults res = d.decompileFunction(f, 120, monitor);
                if (res == null || !res.decompileCompleted()) {
                    emit("   decompile failed: " + (res == null ? "null" : res.getErrorMessage()));
                } else {
                    emit(res.getDecompiledFunction().getC());
                }
                emit("---- listing ----");
                InstructionIterator it = currentProgram.getListing().getInstructions(f.getBody(), true);
                int n = 0;
                while (it.hasNext() && n < 900) {
                    Instruction ins = it.next();
                    emit(String.format("   %s  %s", ins.getAddress(), ins.toString()));
                    n++;
                }
            }
        }
        if (outPath != null) {
            PrintWriter pw = new PrintWriter(outPath, "UTF-8");
            for (String s : buf) {
                pw.println(s);
            }
            pw.close();
            println("[zf_fn] wrote " + outPath);
        }
    }
}
