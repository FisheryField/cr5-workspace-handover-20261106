# reboot_probe.ps1 - capture the zero/encoder fingerprint BEFORE and AFTER a cabinet power cycle
# Usage: powershell -ExecutionPolicy Bypass -File tools\reboot_probe.ps1
param(
  [string]$Prefix = "zp_$(Get-Date -Format yyyyMMdd_HHmmss)",
  [int]$BootTimeoutSec = 420
)
$ErrorActionPreference = "Continue"
$ws   = Split-Path -Parent $PSScriptRoot
$dest = Join-Path $ws "data\reboot_probe"
New-Item -ItemType Directory -Force -Path $dest | Out-Null
$env:SSH_ASKPASS = "$ws\.askpass.cmd"
$env:SSH_ASKPASS_REQUIRE = "force"
$sshOpts = @("-o","StrictHostKeyChecking=no","-o","UserKnownHostsFile=$ws\.ssh_agent\known_hosts",
             "-o","PreferredAuthentications=password","-o","NumberOfPasswordPrompts=1","-o","ConnectTimeout=6")
function RExec([string]$c) { & ssh @sshOpts "root@192.168.5.1" $c 2>&1 }

Write-Host "=== [0/6] upload zeroprobe.sh ===" -ForegroundColor Cyan
& "$ws\rscp.cmd" -q "$PSScriptRoot\zeroprobe.sh" "root@192.168.5.1:/tmp/zeroprobe.sh" 2>&1 | Out-Null
RExec "chmod +x /tmp/zeroprobe.sh; rm -rf /tmp/zp_* /tmp/zeroprobe_*; df -h /tmp | tail -1"

$tagA = $Prefix + "_before"
$tagB = $Prefix + "_after"

Write-Host "=== [1/6] PHASE A: snapshot BEFORE power cycle ===" -ForegroundColor Cyan
RExec "/tmp/zeroprobe.sh $tagA | tail -4"
& "$ws\rscp.cmd" -q "root@192.168.5.1:/tmp/$tagA.tar.gz" "$dest" 2>&1
tar -xzf "$dest\$tagA.tar.gz" -C $dest 2>&1
Write-Host "   A saved: $dest\$tagA" -ForegroundColor Green

Write-Host ""
Write-Host "############################################################" -ForegroundColor Yellow
Write-Host "#  现在请【整柜物理断电】（切断控制箱总电源）                #" -ForegroundColor Yellow
Write-Host "#  等 10 秒，再重新上电。                                  #" -ForegroundColor Yellow
Write-Host "#  脚本会自动等待控制柜起来，然后采集第二份指纹。           #" -ForegroundColor Yellow
Write-Host "#  （不要只重启控制器，要断开总电源）                      #" -ForegroundColor Yellow
Write-Host "############################################################" -ForegroundColor Yellow
Write-Host ""
Read-Host "断电并重新上电后，按 Enter 继续"

Write-Host "=== [2/6] waiting for the controller to come back ===" -ForegroundColor Cyan
$deadline = (Get-Date).AddSeconds($BootTimeoutSec)
$up = $false
while ((Get-Date) -lt $deadline) {
  $r = (RExec "pidof codesyscontrol >/dev/null 2>&1 && echo DSH_READY || echo DSH_NOTREADY") -join " "
  if ($r -match "DSH_READY") { $up = $true; break }
  Write-Host ("  ... still down ({0})" -f (Get-Date -Format "HH:mm:ss"))
  Start-Sleep -Seconds 10
}
if (-not $up) { Write-Host "TIMEOUT: controller did not come back in $BootTimeoutSec s" -ForegroundColor Red; exit 1 }
Write-Host "   codesyscontrol is up" -ForegroundColor Green
Write-Host "=== [3/6] let the application settle (45 s) ===" -ForegroundColor Cyan
Start-Sleep -Seconds 45

Write-Host "=== [4/6] PHASE B: snapshot AFTER power cycle ===" -ForegroundColor Cyan
RExec "/tmp/zeroprobe.sh $tagB | tail -4"
& "$ws\rscp.cmd" -q "root@192.168.5.1:/tmp/$tagB.tar.gz" "$dest" 2>&1
tar -xzf "$dest\$tagB.tar.gz" -C $dest 2>&1
Write-Host "   B saved: $dest\$tagB" -ForegroundColor Green

Write-Host "=== [5/6] compare ===" -ForegroundColor Cyan
$py = "C:\Program Files\PyManager\python.exe"
$cmp = Join-Path $PSScriptRoot "compare_zeroprobe.py"
& $py $cmp (Join-Path $dest $tagA) (Join-Path $dest $tagB)

Write-Host ""
Write-Host "=== [6/6] raw state.txt diff ===" -ForegroundColor Cyan
$a = Join-Path $dest "$tagA\state.txt"
$b = Join-Path $dest "$tagB\state.txt"
if ((Test-Path $a) -and (Test-Path $b)) {
  Write-Host "--- A: homeEncoder.json + versions ---"
  Select-String -Path $a -Pattern '"servo|"time"|"date"|base_hex' | Select-Object -First 20 | ForEach-Object { "  " + $_.Line.Trim() }
  Write-Host "--- B: homeEncoder.json + versions ---"
  Select-String -Path $b -Pattern '"servo|"time"|"date"|base_hex' | Select-Object -First 20 | ForEach-Object { "  " + $_.Line.Trim() }
}
Write-Host ""
Write-Host "DONE. results under: $dest" -ForegroundColor Green
