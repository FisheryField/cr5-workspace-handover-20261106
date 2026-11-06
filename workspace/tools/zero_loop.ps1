# zero_loop.ps1 - closed loop: fingerprint -> calibrate -> fingerprint -> power cycle -> fingerprint
# Usage: powershell -ExecutionPolicy Bypass -File tools\zero_loop.ps1
param(
  [string]$Prefix = "zl_$(Get-Date -Format yyyyMMdd_HHmmss)",
  [int]$BootTimeoutSec = 420,
  [switch]$SkipPowerCycle
)
$ErrorActionPreference = "Continue"
$ws   = Split-Path -Parent $PSScriptRoot
$dest = Join-Path $ws "data\zero_loop"
New-Item -ItemType Directory -Force -Path $dest | Out-Null
$env:SSH_ASKPASS = "$ws\.askpass.cmd"
$env:SSH_ASKPASS_REQUIRE = "force"
$sshOpts = @("-o","StrictHostKeyChecking=no","-o","UserKnownHostsFile=$ws\.ssh_agent\known_hosts",
             "-o","PreferredAuthentications=password","-o","NumberOfPasswordPrompts=1","-o","ConnectTimeout=6")
function RExec([string]$c) { & ssh @sshOpts "root@192.168.5.1" $c 2>&1 }

function Snap([string]$tag) {
  Write-Host "--- snapshot: $tag ---" -ForegroundColor Cyan
  RExec "/tmp/zeroprobe.sh $tag | tail -2"
  & "$ws\rscp.cmd" -q "root@192.168.5.1:/tmp/$tag.tar.gz" "$dest" 2>&1 | Out-Null
  tar -xzf "$dest\$tag.tar.gz" -C $dest 2>&1 | Out-Null
  if (Test-Path "$dest\$tag\state.txt") { Write-Host "   ok -> $dest\$tag" -ForegroundColor Green }
  else { Write-Host "   FAILED" -ForegroundColor Red }
}

Write-Host "=== [0/7] upload + clean /tmp ===" -ForegroundColor Cyan
& "$ws\rscp.cmd" -q "$PSScriptRoot\zeroprobe.sh" "root@192.168.5.1:/tmp/zeroprobe.sh" 2>&1 | Out-Null
RExec "chmod +x /tmp/zeroprobe.sh; rm -rf /tmp/zl_* /tmp/zp_*; df -h /tmp | tail -1"

Write-Host "=== [1/7] S0: current state (NOT calibrated) ===" -ForegroundColor Cyan
Snap ($Prefix + "_s0_before_calib")

Write-Host ""
Write-Host "############################################################" -ForegroundColor Yellow
Write-Host "#  STEP 2: do ONE zero calibration now                     #" -ForegroundColor Yellow
Write-Host "#    - robot must be ENABLED                               #" -ForegroundColor Yellow
Write-Host "#    - maintenance tool -> zero calibration,  or:          #" -ForegroundColor Yellow
Write-Host "#      Invoke-WebRequest http://192.168.5.1:22000/calibrate/home -Method POST -Body '{}' -ContentType 'application/json' -UseBasicParsing" -ForegroundColor Gray
Write-Host "############################################################" -ForegroundColor Yellow
Read-Host "标定完成后按 Enter"

Write-Host "=== [3/7] S1: right after calibration ===" -ForegroundColor Cyan
Snap ($Prefix + "_s1_after_calib")

if (-not $SkipPowerCycle) {
  Write-Host ""
  Write-Host "############################################################" -ForegroundColor Yellow
  Write-Host "#  STEP 4: power cycle the cabinet NOW                     #" -ForegroundColor Yellow
  Write-Host "#    - cut the MAIN power, wait 10 s, power on again       #" -ForegroundColor Yellow
  Write-Host "############################################################" -ForegroundColor Yellow
  Read-Host "断电并重新上电后按 Enter"

  Write-Host "=== [5/7] waiting for controller ===" -ForegroundColor Cyan
  $deadline = (Get-Date).AddSeconds($BootTimeoutSec); $up = $false
  while ((Get-Date) -lt $deadline) {
    $r = (RExec "pidof codesyscontrol >/dev/null 2>&1 && echo DSH_READY || echo DSH_NOTREADY") -join " "
    if ($r -match "DSH_READY") { $up = $true; break }
    Write-Host ("  ... down ({0})" -f (Get-Date -Format "HH:mm:ss"))
    Start-Sleep -Seconds 10
  }
  if (-not $up) { Write-Host "TIMEOUT waiting for controller" -ForegroundColor Red; exit 1 }
  Write-Host "   up; settling 45 s ..." -ForegroundColor Green
  Start-Sleep -Seconds 45

  Write-Host "=== [6/7] S2: after power cycle ===" -ForegroundColor Cyan
  Snap ($Prefix + "_s2_after_reboot")
}

Write-Host "=== [7/7] compare ===" -ForegroundColor Cyan
$dirs = @()
foreach ($s in @("_s0_before_calib","_s1_after_calib","_s2_after_reboot")) {
  $d = Join-Path $dest ($Prefix + $s)
  if (Test-Path $d) { $dirs += $d }
}
$py  = "C:\Program Files\PyManager\python.exe"
$cmp = Join-Path $PSScriptRoot "compare_multi.py"
& $py $cmp @dirs

Write-Host ""
Write-Host "DONE. results under: $dest" -ForegroundColor Green
Write-Host "判读: 若 s1 的 page132 f1 由 0 变为非零、且 s2 又归零 -> 该字段即零点偏移量的落点" -ForegroundColor Green
