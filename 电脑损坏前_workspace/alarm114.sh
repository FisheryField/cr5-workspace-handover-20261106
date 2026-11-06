echo "=== controller alarm id 114 ==="
grep -a -n -A8 '"id" *: *114' /dobot/userdata/project/properties/alarm_controller.json 2>/dev/null | head -40
echo "=== any alarm with 114 ==="
grep -a -n -B3 -A8 '114' /dobot/userdata/project/properties/alarm_controller.json 2>/dev/null | head -60
echo "=== servo alarm 114 ==="
grep -a -n -A8 '"id" *: *114' /dobot/userdata/project/properties/alarm_servo.json 2>/dev/null | head -30