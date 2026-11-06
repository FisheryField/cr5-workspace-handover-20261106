@echo off
rem CR5 servo-zero patch, one-click entry (2026-09-25).
rem All Chinese output lives in the Python script; keep this file ASCII-only.
cd /d "%~dp0.."
echo ==================================================
echo  CR5 zero-point patch (after calibration) - oneclick
echo  Target: controller 192.168.5.1, controller-side only
echo ==================================================
python tools\servo_zero_oneclick.py
echo.
pause
