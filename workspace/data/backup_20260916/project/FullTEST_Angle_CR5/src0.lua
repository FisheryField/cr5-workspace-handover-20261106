local file = io.open("/dobot/userdata/project/project/FullTEST_Angle_CR5/guanjiedianwei.txt","w+")

for i=1,50 do
	Go(_G["P"..i],"SYNC=1")
	Wait(3000)
	Jointparams = GetAngle()
	for k=1,6 do
		file : write (tostring(Jointparams.joint[k]))
		file : write ("\t")			
	end
	file: write ("\n")
	file: flush()
	Sleep(100)
	
	end
file: close()
