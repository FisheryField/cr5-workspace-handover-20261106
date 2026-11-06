--WARNING!:Please keep enough room for the CR5 arm to move

--1.About "Go" Command
Go(P1)--initial point
Go(P2)--end point
Wait(3000)--Script waits for 3s

--2.About "Move" Command
Move(P1)--initial point
Move(P2)--end point
Wait(3000)--Script waits for 3s

--3.About "MoveJ" Command
--Create joint variables
local StarPoint = {joint={0,0,0,0,0,0}} 
local EndPoint = {joint={90,0,-90,0,90,0}} 
--Joint movement
MoveJ(StarPoint)
MoveJ(EndPoint)
Wait(3000)--Script waits for 3s

--4.About "Arc3" Command
Go(P1)--initial point
Arc3(P3,P4)--"P3" It's the middle point of the arc,"P4"It's the end point of the arc
Wait(3000)--Script waits for 3s

--5.About "Circle3" Command
Go(P1)--initial point
Circle3(P3,P4,1)--"P3" It's the middle point of the Circle,"P4"It's the end point of the Circle,"1"On behalf of the number of turns
Wait(3000)--Script waits for 3s

--6.About "Jump" Command
Go(P1)--initial point
Jump(P5,"Start=20 ZLimit=500 End=20")--end point
Wait(3000)--Script waits for 3s

--7.About "RP" Command
Go(P1)--initial point
Go(RP(P1,{0,0,100}))-- The displacement is 100 on the Z-axis at P1
Wait(3000)--Script waits for 3s

--8.About "RJ" Command
local StarPoint = {joint={0,0,0,0,0,0}} --initial point variables
MoveJ(StarPoint)
MoveJ(RJ(StarPoint,{90,0,-90,0,90,0}))--Offset joint motion on Starpoint
Wait(3000)--Script waits for 3s

--9.About "GoR" Command
Go(P1)--initial point
GoR(P1,{0,50,0})--The displacement is 50 on the Y-axis at P1
Wait(3000)--Script waits for 3s

--10.About "MoveR" Command
Go(P1)--initial point
MoveR(P1,{50,0,0})--The displacement is 50 on the X-axis at P1
Wait(3000)--Script waits for 3s

--11.About "MoveJR" Command
local StarPoint = {joint={0,0,0,0,0,0}} --initial point variables
MoveJ(StarPoint)
MoveJR(StarPoint,{90,0,-90,0,90,0})--Offset joint motion on Starpoint
Wait(3000)--Script waits for 3s
