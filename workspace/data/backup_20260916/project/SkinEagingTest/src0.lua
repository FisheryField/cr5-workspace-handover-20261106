Speed(100)
Accel(100)
SetSafeSkin(0)
Sleep(200)
MoveJ({joint={0,0,0,0,0,0}},"Speed=30 Accel=30 SYNC=1")
	Go(P1,"SYNC=1")
	SetSafeSkin(1)
while(true)
	do
	Go(P1,"SYNC=1")
	SetSafeSkin(1)
	for i=1,3 do
	Go(P2)
	Go(P1)
	end
	for i=1,3 do
	Go(P2)
	Go(P3)
	end
	for y=1,3 do
	Go(P3)
	Go(P4)
	end
	for o=1,3 do
	Go(P4)
	Go(P5)
	end
	for i=1,3 do
	Go(P5)
	Go(P6)
	Go(P7)
	end
	for h=1,3 do
	Go(P7)
	Go(P8)
	Go(P9)
	end
	for o=1,3 do
	Go(P18)
	Go(P17)
	end
	Go(P18,"SYNC=1")
	SetSafeSkin(0)
	Go(P10,"SYNC=1")
	SetSafeSkin(1)
	for p=1,3 do
	Go(P11)
	Go(P10)
	end
	for t=1,3 do
	Go(P11)
	Go(P12)
	end
	for j=1,3 do
	Go(P12)
	Go(P13)
	end
	for h=1,3 do
	Go(P13)
	Go(P14)
	end
	for i=1,3 do
	Go(P15)
	Go(P16)
	end
	Go(P15,"SYNC=1")
	SetSafeSkin(0)
	Sleep(100)
	end
