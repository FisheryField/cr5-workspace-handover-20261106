mkdir -p /dobot/userdata/codesys/STAGED_fixed_all6
echo "=== staged dir ==="; ls -la /dobot/userdata/codesys/STAGED_fixed_all6/
echo "=== current variant ==="; cat /tmp/codesysBoot
echo "=== live app ==="; md5sum /dobot/userdata/codesys/allST/Application.app