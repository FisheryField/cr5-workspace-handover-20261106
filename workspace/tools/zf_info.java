// zf_info.java - dump memory blocks, function count, symbols of the current program
// @category servo

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.mem.MemoryBlock;
import ghidra.program.model.symbol.Symbol;
import ghidra.program.model.symbol.SymbolIterator;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;

public class zf_info extends GhidraScript {
    @Override
    public void run() throws Exception {
        println("program=" + currentProgram.getName()
                + " imageBase=" + currentProgram.getImageBase()
                + " lang=" + currentProgram.getLanguageID());
        for (MemoryBlock b : currentProgram.getMemory().getBlocks()) {
            println(String.format("  block %-12s %s..%s  size=0x%x  r=%b w=%b x=%b init=%b",
                    b.getName(), b.getStart(), b.getEnd(), b.getSize(),
                    b.isRead(), b.isWrite(), b.isExecute(), b.isInitialized()));
        }
        int nf = 0;
        FunctionIterator fi = currentProgram.getFunctionManager().getFunctions(true);
        while (fi.hasNext()) { fi.next(); nf++; }
        println("functions=" + nf);
        int ns = 0;
        SymbolIterator si = currentProgram.getSymbolTable().getAllSymbols(true);
        while (si.hasNext()) { Symbol s = si.next(); ns++;
            if (ns <= 30) println("  sym " + s.getAddress() + " " + s.getName()); }
        println("symbols=" + ns);
        // probe a few addresses
        long[] probes = {0x080117d0L, 0x08011810L, 0x08001708L, 0x080045a8L, 0x08010000L};
        for (long p : probes) {
            Address a = toAddr(p);
            Function f = getFunctionContaining(a);
            println(String.format("  probe %08x: inMemory=%b func=%s instr=%s",
                    p, currentProgram.getMemory().contains(a),
                    f == null ? "-" : f.getName(),
                    currentProgram.getListing().getInstructionAt(a)));
        }
    }
}
