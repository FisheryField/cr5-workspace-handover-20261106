local initial = GetAngle()
if type(initial) ~= "table" or type(initial.joint) ~= "table" then
    error("START_FEEDBACK_UNAVAILABLE")
end
for axis = 1, 6 do
    local angle = initial.joint[axis]
    if type(angle) ~= "number" or math.abs(angle) > 0.05 then
        error("START_NOT_ZERO")
    end
end
local target = {joint={15.906764173,-63.542990570,66.598558926,-93.225024985,90.382021185,-73.896999561}}
MoveJ(target, "CP=0 Speed=5 Accel=10 SYNC=1")
local final = GetAngle()
for axis = 1, 6 do
    if math.abs(final.joint[axis] - target.joint[axis]) > 0.2 then
        error("P1_JOINT_MISMATCH")
    end
end
print("ZERO_TO_P1_COMPLETE")
