Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Win32 {
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
}
"@
$p = Get-Process | Where-Object { $_.Name -match 'RoboDK' -and $_.MainWindowHandle -ne 0 } | Select-Object -First 1
if ($p) {
  [Win32]::ShowWindow($p.MainWindowHandle, 9) | Out-Null   # SW_RESTORE
  [Win32]::SetForegroundWindow($p.MainWindowHandle) | Out-Null
  Start-Sleep -Milliseconds 800
  Write-Output "foreground: $($p.Name) pid=$($p.Id)"
} else {
  Write-Output "RoboDK window not found"
}
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$vs = [System.Windows.Forms.SystemInformation]::VirtualScreen
$bmp = New-Object System.Drawing.Bitmap($vs.Width, $vs.Height)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($vs.X, $vs.Y, 0, 0, $bmp.Size)
$out = 'D:\mydata\glm-workplace\data\screens\rdk_screen2.png'
$bmp.Save($out, [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose()
Write-Output "saved $out"
