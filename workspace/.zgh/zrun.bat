@echo off
rem zrun.bat <project-dir> <program> [z_gh.java args...]
set "JAVA_HOME=D:\software\disassembly\jdk21\jdk-21.0.12.1+1"
set "PRJ=%~1"
set "PRG=%~2"
shift
shift
call "D:\software\disassembly\ghidra\ghidra_12.1.4_PUBLIC\support\analyzeHeadless.bat" "%PRJ%" "%PRG%" -process "%PRG%" -noanalysis -scriptPath "D:\mydata\workspace\.zgh" -postScript z_gh.java %1 %2 %3 %4 %5 %6 %7 %8 %9 %10 %11 %12 %13 %14 %15 %16 %17 %18 %19 %20 > "D:\mydata\workspace\.zgh\last.log" 2>&1
findstr /C:"z_gh.java>" "D:\mydata\workspace\.zgh\last.log"
