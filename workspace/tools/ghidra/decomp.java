import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;

public class decomp extends GhidraScript {
    public void run() throws Exception {
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        for (Function f : currentProgram.getFunctionManager().getFunctions(true)) {
            if (f.getName().contains("parseAndReqSetServoParams") && f.getBody().getNumAddresses() > 100) {
                println("##### " + f.getName() + " @ " + f.getEntryPoint() + " #####");
                DecompileResults r = di.decompileFunction(f, 90, monitor);
                if (r.decompileCompleted()) println(r.getDecompiledFunction().getC());
                else println("DECOMP FAIL: " + r.getErrorMessage());
            }
        }
    }
}