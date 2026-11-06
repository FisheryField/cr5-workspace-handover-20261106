# zero_capture.ps1 - one-shot capture: upload -> start on controller -> wait -> fetch -> extract
# Usage: powershell -ExecutionPolicy Bypass -File tools\zero_capture.ps1 -Duration 90
param(
  [string]$Tag = "zero_shm_$(Get-Date -Format yyyyMMdd_HHmmss)",
  [int]$Duration = 90,
  [switch]$Full
)

$ErrorActionPreference = "Continue"
$ws = Split-Path -Parent $PSScriptRoot
$sh = Join-Path $PSScriptRoot "shm_zero_capture.sh"
$mode = if ($Full) { "--full" } else { "" }
$dest = Join-Path $ws "data\captures"
New-Item -ItemType Directory -Force -Path $dest | Out-Null

Write-Host "=== [1/5] upload capture script ===" -ForegroundColor Cyan
& "$ws\rscp.cmd" -q "$sh" "root@192.168.5.1:/tmp/shm_zero_capture.sh" 2>&1 | Out-Null

Write-Host "=== [2/5] start capture in background on controller ===" -ForegroundColor Cyan
$env:SSH_ASKPASS = "$ws\.askpass.cmd"
$env:SSH_ASKPASS_REQUIRE = "force"
$sshOpts = @("-o","StrictHostKeyChecking=no","-o","UserKnownHostsFile=$ws\.ssh_agent\known_hosts",
             "-o","PreferredAuthentications=password","-o","NumberOfPasswordPrompts=1","-o","ConnectTimeout=15")
$remote = "chmod +x /tmp/shm_zero_capture.sh; rm -f /tmp/$Tag.tar.gz /tmp/$Tag.launch.log; " +
          "nohup /tmp/shm_zero_capture.sh $Tag $Duration $mode > /tmp/$Tag.launch.log 2>&1 & sleep 3; " +
          "echo STARTED; head -4 /tmp/$Tag.launch.log"
& ssh @sshOpts "root@192.168.5.1" $remote 2>&1

Write-Host ""
Write-Host "############################################################" -ForegroundColor Yellow
Write-Host "#  NOW: perform ONE zero calibration within $Duration seconds      #" -ForegroundColor Yellow
Write-Host "#    - keep the robot ENABLED (RobotMode=5)                #" -ForegroundColor Yellow
Write-Host "#    - run zero calibration (maintenance tool, or          #" -ForegroundColor Yellow
Write-Host "#      POST http://192.168.5.1:22000/calibrate/home )      #" -ForegroundColor Yellow
Write-Host "#  The capture is READ-ONLY and will not affect the result.#" -ForegroundColor Yellow
Write-Host "############################################################" -ForegroundColor Yellow
Write-Host ""

$wait = $Duration + 30
Write-Host "=== [3/5] waiting $wait s (countdown below) ===" -ForegroundColor Cyan
for ($i = $wait; $i -gt 0; $i--) {
  Write-Host ("  remaining: {0,4} s " -f $i)
  Start-Sleep -Seconds 1
}

Write-Host "=== [4/5] fetch result ===" -ForegroundColor Cyan
& "$ws\rscp.cmd" -q "root@192.168.5.1:/tmp/$Tag.tar.gz" "$dest" 2>&1
$tgz = Join-Path $dest "$Tag.tar.gz"
if (-not (Test-Path $tgz)) { Write-Host "FETCH FAILED: $tgz missing" -ForegroundColor Red; exit 1 }

Write-Host "=== [5/5] extract ===" -ForegroundColor Cyan
$ex = Join-Path $dest $Tag
New-Item -ItemType Directory -Force -Path $ex | Out-Null
tar -xzf $tgz -C $ex 2>&1
Write-Host ""
Write-Host "DONE. output: $ex" -ForegroundColor Green
Get-ChildItem -Recurse -File $ex | Measure-Object -Property Length -Sum |
  ForEach-Object { Write-Host ("  {0} files / {1:N1} MB" -f $_.Count, ($_.Sum/1MB)) }
$ch = Get-ChildItem -Recurse -File $ex -Filter "changes.txt" | Select-Object -First 1
if ($ch) {
  Write-Host ""
  Write-Host "--- changes.txt (first 20 lines) ---" -ForegroundColor Cyan
  Get-Content $ch.FullName -TotalCount 20
} else {
  Write-Host "(no changes.txt - nothing changed)" -ForegroundColor Yellow
}
Write-Host ""
Write-Host "Tell me the path: $ex" -ForegroundColor Green
