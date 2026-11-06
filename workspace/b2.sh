chmod +x /tmp/amscan
ls -l /tmp/amscan /tmp/app_anchors.txt
echo "=== run ==="
/tmp/amscan 376 /tmp/app_anchors.txt
echo "=== rc=$? ==="
