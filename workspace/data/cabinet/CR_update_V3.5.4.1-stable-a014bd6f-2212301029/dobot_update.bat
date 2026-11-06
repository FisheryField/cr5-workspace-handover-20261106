@echo off
cd ./src
cd %~d0
set server_ip=192.168.5.1

set date=%date:~0,4%-%date:~5,2%-%date:~8,2%
set time=%time:~0,2%:%time:~3,2%:%time:~6,2%
echo time now is %date% %time%
plink.exe -ssh -l root -pw [REDACTED] %server_ip% rm /etc/localtime
plink.exe -ssh -l root -pw [REDACTED] %server_ip% ln -s /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
plink.exe -ssh -l root -pw [REDACTED] %server_ip% date -s %date%
plink.exe -ssh -l root -pw [REDACTED] %server_ip% date -s %time%
plink.exe -ssh -l root -pw [REDACTED] %server_ip% hwclock -w -u
pscp.exe -pw [REDACTED] -r i2cset root@%server_ip%:/tmp
plink.exe -ssh -l root -pw [REDACTED] %server_ip% chmod +x /tmp/i2cset
plink.exe -ssh -l root -pw [REDACTED] %server_ip% /tmp/i2cset -f -y 2 0x51 0x01 0x7 b
echo set time done !

@REM @set /p var="Do you update MG6?(y/n)"
@REM if %var% == y  (
@REM     echo MG6 > robotType
@REM     pscp.exe -pw [REDACTED] -r robotType root@%server_ip%:/dobot/userdata/
@REM     plink.exe -ssh -l root -pw [REDACTED] %server_ip% dos2unix /dobot/userdata/robotType
@REM     plink.exe -ssh -l root -pw [REDACTED] %server_ip% ln -snf /dobot/userdata/MG6_sys_files/project /dobot/userdata/
@REM )

plink.exe -ssh -l root -pw [REDACTED] %server_ip% "free | awk 'NR==2{print $2}'" > memsize
for /f "delims=" %%i in (memsize) do (set size=%%i)&(goto :next)
:next
del memsize
echo memory is %size% KB
if %size% LEQ 1025000 (
	echo "u-boot is ok....";    
    
    echo delete the point file
    plink.exe -ssh -l root -pw [REDACTED] %server_ip% rm -r /home/ftp/PlcLogic/Recipe/SavePos.txt

    echo uploading firmware ...
    pscp.exe -pw [REDACTED] -r bin.tar.gz       root@%server_ip%:/tmp/
    pscp.exe -pw [REDACTED] -r afterUpdate.sh   root@%server_ip%:/tmp/    

    echo write to disk ...
    plink.exe -ssh -l root -pw [REDACTED] %server_ip% chmod +x /tmp/afterUpdate.sh
    plink.exe -ssh -l root -pw [REDACTED] %server_ip% /tmp/afterUpdate.sh
    plink.exe -ssh -l root -pw [REDACTED] %server_ip% sync
    
    color 2
    echo " *  ____                                             _  * "
    echo " * / ___|   _   _    ___    ___    ___   ___   ___  | | * "
    echo " * \___ \  | | | |  / __|  / __|  / _ \ / __| / __| | | * "
    echo " *  ___) | | |_| | | (__  | (__  |  __/ \__ \ \__ \ |_| * "
    echo " * |____/   \__,_|  \___|  \___|  \___| |___/ |___/ (_) * "
    echo " *                                                      * "
    echo The upgrade has been completed. Please power off the robot and power on again!
) else (
    color 4
    echo " *  _____           _   _               _   _  * "
    echo " * |  ___|   __ _  (_) | |   ___     __| | | | * "
    echo " * | |_     / _` | | | | |  / _ \   / _  | | | * "
    echo " * |  _|   | (_| | | | | | |  __/  | (_| | |_| * "
    echo " * |_|      \__,_| |_| |_|  \___|   \__,_| (_) * "
    echo " *                                             * "
    echo " *                                             * "
    echo " *                                             * "
    echo " *                                             * "
    echo update failed, you have to update u-boot first .....
    echo " *                                             * "
)

@REM TIMEOUT /T 20 /NOBREAK
pause