F=/dobot/userdata/project/settings/function/homeEncoder.json
cp -f $F ${F}.bak_$(date +%H%M%S) 2>/dev/null || cp -f $F /tmp/homeEncoder.json.bak
ls -la /dobot/userdata/project/settings/function/homeEncoder.json* | tail -5
