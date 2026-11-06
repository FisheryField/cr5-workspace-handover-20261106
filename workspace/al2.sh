for id in 96 99 102 105 108 111 131 12294; do
  echo "--- controller alarm $id ---"
  grep -a -A6 "\"id\": $id," /dobot/userdata/project/properties/alarm_controller.json 2>/dev/null | head -8
done
echo "=== servo alarm 60948 ==="
grep -a -A6 "\"id\": 60948," /dobot/userdata/project/properties/alarm_servo.json 2>/dev/null | head -10
echo "=== servo alarm 0xEE14 / ee14 ==="
grep -a -i -A6 "ee14" /dobot/userdata/project/properties/alarm_servo.json 2>/dev/null | head -10