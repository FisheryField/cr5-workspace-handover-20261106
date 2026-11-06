--WARNING!:Please keep enough room for the CR5 arm to move
--Main program run
Go(P6)
while true do
	Go(P1,"Accel=100 Speed=100")
	if (i>=0 and i<6)
	then
	Go(P3)
	print("Going")
	else
	Go(P2)
	print("OVER")
	break
	end
	end
