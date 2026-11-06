$ErrorActionPreference='Continue'
[Console]::OutputEncoding=[System.Text.Encoding]::UTF8
$gbk=[System.Text.Encoding]::GetEncoding(936)
$b='D:\software\DobotStudio\V1.3.4-stable\V1.3.4-stable\upgradeFiles\3.5.6\3.5.6.1\servoCSV\'
$p1=$b+'CR\CR5\J1.csv'
$p2=$b+'CR\param.csv'
$t1=$gbk.GetString([System.IO.File]::ReadAllBytes($p1)); $l1=$t1.Split([char]10)
$t2=$gbk.GetString([System.IO.File]::ReadAllBytes($p2)); $l2=$t2.Split([char]10)
Write-Output '===== CR5/J1.csv (lines '+$l1.Count+') ====='
$l1[0..69] -join [char]10
Write-Output ''
Write-Output '===== CR/param.csv (lines '+$l2.Count+') ====='
$l2[0..59] -join [char]10