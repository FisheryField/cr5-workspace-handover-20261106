-- Read-only diagnostic: no motion, I/O, or controller settings commands.
local function dump(path, value, depth)
    if type(value) ~= "table" then
        print(path .. "=" .. tostring(value))
        return
    end
    if depth == 0 then return end
    for key, field in pairs(value) do
        dump(path .. "." .. tostring(key), field, depth - 1)
    end
end

local function capture(name, ...)
    print(name .. "_RETURN_COUNT=" .. tostring(select("#", ...)))
    for i = 1, select("#", ...) do
        dump(name .. "[" .. tostring(i) .. "]", select(i, ...), 3)
    end
end

capture("GET_ANGLE", GetAngle())
capture("GET_POSE", GetPose())
print("CHECKMOVE_EXPORTED=" .. tostring(type(CheckMove) == "function"))
print("MOVE_EXPORTED=" .. tostring(type(Move) == "function"))
print("FIRST_MOVEL_POSE_PROBE_DONE")
