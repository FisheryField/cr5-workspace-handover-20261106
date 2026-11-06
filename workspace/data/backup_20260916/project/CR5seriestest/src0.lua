local A ={joint={175,90,-125,-90,-120,175}}
local B ={joint={-175,-90,125,90,120,-175}}
local Home={joint={0,0,0,0,0,0}}
Speed(100)
Accel(100)
MoveJ(Home,"Speed=30 Accel=30 SYNC=1")
while(true)
	do
MoveJ(A)
MoveJ(B)
	end