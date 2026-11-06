echo "===== PROCESSES ====="; ps w 2>/dev/null || ps aux 2>/dev/null || ps
echo "===== LISTENING PORTS ====="; netstat -tlnp 2>/dev/null || netstat -tln 2>/dev/null
echo "===== INITTAB ====="; cat /etc/inittab 2>/dev/null
echo "===== /etc/init.d ====="; ls -la /etc/init.d 2>/dev/null
echo "===== /etc/rc.d ====="; ls -la /etc/rc.d 2>/dev/null
echo "===== rc.local ====="; cat /etc/rc.local 2>/dev/null
echo "===== PASSWD ====="; cat /etc/passwd 2>/dev/null
echo "===== /dobot ====="; ls -la /dobot 2>/dev/null
echo "===== /dobot/bin ====="; ls -la /dobot/bin 2>/dev/null
echo "===== /project (target) ====="; ls -la /dobot/bin/project 2>/dev/null
echo "===== /mToolServer ====="; ls -laR /mToolServer 2>/dev/null | head -60
echo "===== /web ====="; ls -laR /web 2>/dev/null | head -50
echo "===== /opt/save.sh ====="; cat /opt/save.sh 2>/dev/null
echo "===== /opt/.zero ====="; cat /opt/.zero 2>/dev/null
echo "===== /opt/codesys ====="; ls -la /opt/codesys 2>/dev/null
echo "===== /usr/local/{bin,sbin,etc} ====="; ls -la /usr/local/bin /usr/local/sbin /usr/local/etc 2>/dev/null
echo "===== /root subdirs ====="; ls -la /root/Settings /root/Documents /root/download 2>/dev/null
echo "===== .ash_history (tail) ====="; tail -40 /root/.ash_history 2>/dev/null