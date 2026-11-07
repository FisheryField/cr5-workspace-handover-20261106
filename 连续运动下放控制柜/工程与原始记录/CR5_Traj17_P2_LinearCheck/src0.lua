local function checked_joints(expected, tolerance, label)
    local feedback = GetAngle()
    if type(feedback) ~= "table" or type(feedback.joint) ~= "table" then
        error(label .. "_FEEDBACK_UNAVAILABLE")
    end
    for axis = 1, 6 do
        local angle = feedback.joint[axis]
        if type(angle) ~= "number" or math.abs(angle - expected[axis]) > tolerance then
            error(label .. "_JOINT_MISMATCH_AXIS_" .. axis)
        end
    end
    return feedback
end

checked_joints({0,0,0,0,0,0}, 0.05, "ZERO")
local p1 = {joint={15.906764173,-63.542990570,66.598558926,-93.225024985,90.382021185,-73.896999561}}
local p2 = {joint={64.021287934,6.446332626,132.246834164,-138.394228018,-63.354553055,-0.324168542}}
local optionsJ = "CP=0 Speed=5 Accel=10 SYNC=1"
MoveJ(p1, optionsJ)
checked_joints(p1.joint, 0.05, "P1")
print("P1_COMPLETE")
MoveJ(p2, optionsJ)
checked_joints(p2.joint, 0.05, "P2")
print("P2_COMPLETE")

local pose = GetPose()
local config = type(pose) == "table" and pose.armOrientation or nil
if type(config) ~= "table" then error("P2_ARM_ORIENTATION_MISSING") end
for axis = 1, 4 do
    local value = config[axis]
    if type(value) ~= "number" or value ~= math.floor(value) or math.abs(value) > 127 then
        error("P2_ARM_ORIENTATION_INVALID_AXIS_" .. axis)
    end
end
print(string.format("P2_ARM_ORIENTATION=%d,%d,%d,%d", config[1], config[2], config[3], config[4]))
local p3 = {coordinate={120.004898830,-421.016639686,420.121370103,-89.983030031,-0.001014634,-179.999991598}, armOrientation={config[1],config[2],config[3],config[4]}, user=0, tool=0}
local optionsL = "User=0 Tool=0 CP=0 SpeedS=1 AccelS=10 SYNC=1"
if type(CheckMove) ~= "function" then error("NATIVE_CHECKMOVE_UNAVAILABLE") end
local ok, result = pcall(CheckMove, p3, optionsL)
print("P3_CHECKMOVE_OK=" .. tostring(ok) .. " RESULT=" .. tostring(result))
checked_joints(p2.joint, 0.05, "P2_AFTER_CHECK")
print("P2_LINEAR_CHECK_COMPLETE")
