echo "=== F tree"
find /home/ftp -maxdepth 3 | head -60
echo "=== F sizes"
du -sh /home/ftp 2>/dev/null
echo "=== F tar"
tar czf /tmp/ftp.tgz -C /home ftp 2>/dev/null; ls -la /tmp/ftp.tgz
echo "=== F done"