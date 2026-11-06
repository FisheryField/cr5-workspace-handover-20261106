local temp = 0x70
local temp1 = 0x60
local A,B,C,D =0,0,0,0
SetToolBaudRate(115200)
temp1 = 0x60
for i=1,2 do
	temp = i-1+temp
	GWrite(0x01,{temp})
	Sleep(500)
local ret = GRead(0x01)
	if ret.buf[1] ==113 then 
		
		print("485  OK")
		Sleep(800)
	elseif ret.buf[1]==114 then
		
		print("485  OK1")
		Sleep(800)
		temp = 0x70
	else
		print("NG")
	end
end
while true do

	for i=1,4 do
		temp1 = 0x60
		temp1 = i-1+temp1
			GWrite(0x01,{temp1})
			Sleep(500)
			ret1 = GRead(0x02,{33,34})
			Sleep(1000)
				if ret1.buf[1] == 1 and i==1 then
					A = A+1
				elseif ret1.buf[1] == 0 and i==2 then
					A = A+1									
				elseif ret1.buf[2] == 1 and i==3 then 
					B = B+1
				elseif ret1.buf[2] == 0 and i==4 then
					B = B+1
				else
					print("Not Get DI"..ret1)
				end
				--print(ret1.buf)
				Sleep(500)
		
	end
	if A == 2 then
		print("DI1 OK")
	else
		print("DI1 NG")
	end
	if B == 2 then
		print("DI2 OK")
	else
		print("DI2 NG")
	end
	Sleep(500)
	temp1=temp1+4
	for i=1,4 do
	  GWrite(0x01,{temp1})
	  Sleep(500)
		
		if i<=2 then 
			GWrite(0x03,{{17,i%2}})
			Sleep(800)
			ret3 = GRead(0x02,{33})			
			--print(ret3.buf)
			Sleep(800)	
				if ret3.buf[1] == 1  then
					C = C+1
				elseif ret3.buf[1] == 0 then
					C = C+1
				else
					print("Get DO1 ERR")
				end
	
		else			
			GWrite(0x03,{{18,i%2}})
			Sleep(500)
			ret4 = GRead(0x02,{34})			
			--print(ret4.buf)
			Sleep(500)			
				if ret4.buf[1] == 1  then
					D = D+1
				elseif ret4.buf[1] == 0  then
					D = D+1
				else
				   print("Get DO2 ERR")
				end
		end
	end
	if C == 2 then
		print("DO1 OK")
		Sleep(800)
	else
		print("DO1 NG")
		Sleep(800)
	end
	Sleep(500)
	if D == 2 then
		print("DO2 OK")
		Sleep(800)
	else
		print("DO2 NG")
		Sleep(800)
	end
	Sleep(500)
	GWrite(0x01,{0x63},"SYNC=1")
A,B,C,D =0,0,0,0	
Pause()
end
