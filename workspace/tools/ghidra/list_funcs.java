import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;

public class list_funcs extends GhidraScript {
    @Override
    public void run() throws Exception {
        println("IMAGE BASE = " + currentProgram.getImageBase());
        FunctionManager fm = currentProgram.getFunctionManager();
        String[] KW = {"parseAndReqSetServoParams","parseAndReqGetServoParams","modifyServoParams",
                       "readServoParams","readSDO","writeSDO","exitSDOWRThd","getAndPackServoParams",
                       "createSDORWThd","readSDOthd","writeSDOthd"};
        int n = 0;
        for (Function f : fm.getFunctions(true)) {
            n++;
            String nm = f.getName();
            for (String k : KW) {
                if (nm.contains(k)) {
                    println("HIT " + nm + " @ " + f.getEntryPoint() + " size=" + f.getBody().getNumAddresses());
                    break;
                }
            }
        }
        println("FUNCTION COUNT = " + n);
    }
}