Speed(100)
Accel(100)
CP(20)
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

local A={joint={-90,-90,90,90,90,90}}
local B={joint={90,90,-90,-90,-90,-90}}
local home={joint={0,0,0,0,0,0}}
local GA={joint={170,90,-60,-90,-100,145}}
local GB={joint={-110,-90,120,90,100,-145}}
local C={joint={120,90,-120,-60,-90,0}}
local D={joint={-50,90,-30,20,90,-90}}
local E={joint={130,0,130,-40,90,0}}
local F={joint={130,50,60,-20,90,-90}}
local G={joint={50,0,130,-40,90,0}}
local H={joint={50,50,60,-20,90,-90}}
local I={joint={-40,0,130,-40,90,0}}
local J={joint={-40,50,60,-20,90,-90}}

setExcitMode(33)

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

local count = 0

while (count < 3) do 
	MoveJ(home)
	for i=1,3 do
		MoveJ(C)
		MoveJ(D)
	end
	MoveJ(home)
	for o=1,5 do
		MoveJ(E)
		MoveJ(F)
	end
	for o=1,5 do
		MoveJ(G)
		MoveJ(H)
	end
	for o=1,5 do
		MoveJ(I)
		MoveJ(J)
	end
	MoveJ(home)
	for p=1,5 do 
		MoveJ(A)
		MoveJ(B)
	end
	MoveJ(home)
	for q=1,10 do
		MoveJ(GA)
		MoveJ(GB)
	end
	count = count + 1
end

DO(1,ON,"SYNC=1")
setExcitMode(3)
DO(1,OFF,"SYNC=1")


