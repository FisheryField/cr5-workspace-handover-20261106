local A ={joint={170,90,-60,-90,-100,145}}
local B ={joint={-110,-90,120,90,100,-145}}
local home={joint={0,0,0,0,0,0}}
local J1just={joint={178,0,0,0,0,0}}
local J1lose={joint={-178,0,0,0,0,0}}
local J2just={joint={0,90,-90,0,0,0}}
local J2lose={joint={0,-90,90,0,0,0}}
local J3just={joint={0,0,140,0,0,0}}
local J3lose={joint={0,0,-140,0,0,0}}
local J4just={joint={0,0,0,90,0,0}}
local J4lose={joint={0,0,0,-90,0,0}}
local J5just={joint={0,0,0,0,178,0}}
local J5lose={joint={0,0,0,0,-178,0}}
local J6just={joint={0,0,0,0,0,178}}
local J6lose={joint={0,0,0,0,0,-178}}
Accel(100)
Speed(100)
while true do
MoveJ(home,"SYNC=1")
MoveJ(J1just)
MoveJ(J1lose)
MoveJ(home)
MoveJ(J2just)
MoveJ(J2lose)
MoveJ(home)
MoveJ(J3just)
MoveJ(J3lose)
MoveJ(home)
MoveJ(J4just)
MoveJ(J4lose)
MoveJ(home)
MoveJ(J5just)
MoveJ(J5lose)
MoveJ(home)
MoveJ(J6just)
MoveJ(J6lose)
MoveJ(home)
MoveJ(A)
MoveJ(B)
end


