
--test
print('======TEST START====')

print("start test:cp(1)")
CP(1)
print("start test:cp(0)")
CP(0)

print("start test:Arch(0)")
Arch(0)
print("start test:Arch(1)")
Arch(1)

print("start test:LimZ(48)")
LimZ(48)

print("start test:SpeedFactor(48)")
SpeedFactor(48)

print("start test:Speed(48)")
Speed(48)

print("start test:Accel(48)")
Accel(48)

print("start test:Jerk(48)")
Jerk(48)

print("start test:SpeedS(48)")
SpeedS(48)

print("start test:SpeedR(48)")
SpeedR(48)

print("start test:AccelS(48)")
AccelS(48)

print("start test:AccelR(48)")
AccelR(48)

print("start test:JerkS(48)")
JerkS(48)

print("start test:JerkR(48)")
JerkR(48)


function Sleep(n)
   os.execute("sleep " .. n)
end

local p1 = {armOrientation = "left", coordinate = {334.9, 31.5, 15, -32, 0, 0}, tool = 0, user = 0}
local p2 = {armOrientation = "left", coordinate = {285.9, -82.7, 15, -32.3, 0, 0}, tool = 0, user = 0}
local p3 = {armOrientation = "left", coordinate = {287.55, -33.5, 15, -24.98, 0, 0}, tool = 0, user = 0}
local p4 = {armOrientation = "left", coordinate = {261, -87.1, 15, -24.98, 0, 0}, tool = 0, user = 0}
local p5 = {armOrientation = "left", coordinate = {215.5, -137.3, 15, -24.98, 0, 0}, tool = 0, user = 0}

--test
print('======TEST START====')

Speed(80)
Accel(60)
Jerk(60)
LimZ(48)
while true do
Go(p1)
Move(p2)
Jump(p3)
Arc3(p4, p5)
end

--print("start test:GetPose()")
--print("GetPose", dobot.GetPose())

print("start test:GetPose()")
print("GetPose", dobot.GetPose())