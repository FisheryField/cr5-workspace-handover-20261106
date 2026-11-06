mkdir -p /dobot/userdata/project/settings/function
if [ ! -f /dobot/userdata/project/settings/function/servoParams.json ]; then
  echo '{"body":[]}' > /dobot/userdata/project/settings/function/servoParams.json
  chmod 666 /dobot/userdata/project/settings/function/servoParams.json
  echo "已创建 servoParams.json"
else
  echo "已存在"
fi
ls -la /dobot/userdata/project/settings/function/servoParams.json
