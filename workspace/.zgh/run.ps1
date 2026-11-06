param(
    [Parameter(Mandatory=$true)][string]$Proj,
    [Parameter(Mandatory=$true)][string]$Prg,
    [Parameter(ValueFromRemainingArguments=$true)][string[]]$Cmds
)
$env:JAVA_HOME = 'D:\software\disassembly\jdk21\jdk-21.0.12.1+1'
& 'D:\software\disassembly\ghidra\ghidra_12.1.4_PUBLIC\support\analyzeHeadless.bat' `
    $Proj $Prg -process $Prg -noanalysis `
    -scriptPath 'D:\mydata\workspace\.zgh' -postScript z_gh.java @Cmds 2>&1 |
    Select-String -Pattern 'z_gh.java>' | ForEach-Object { $_.Line -replace '^.*z_gh\.java> ', '' }
