--WARNING!:Please keep enough room for the CR5 arm to move
Accel(100)	--Set the "Go MoveJ GoR MoveJR" command acceleration ratio
Speed(100)	--Set the "Go MoveJ GoR MoveJR" command speed ratio
AccelS(100)	--Set the "Move Arc3 Circle3 MoveR Jump" acceleration ratio
SpeedS(100)	--Set the "Move Arc3 Circle3 MoveR Jump" command speed ratio
CP(100)		--Sets the smoothness of all movement instructions
--Example:Speed parameters can be changed to observe the motion of CR5
--An infinite loop
for i=1,10 do
Go(P1)
Go(P2)
Move(P1)
Move(P2)
end
while true do
print("Please set the first DI signal high")
if DI(1)==1 then
DO(1,ON)--The first IO signal output
Wait(2000)--Script waits for 3s
DO(2,ON)--The second IO signal output
Wait(2000)
DO(1,OFF)--The first IO signal is off
Wait(2000)
DO(2,OFF)--The second IO signal is off
Wait(2000)
break
end
end
