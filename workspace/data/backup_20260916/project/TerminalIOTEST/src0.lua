local temp = 0x70
local temp1 = 0x60
local A,B,C,D =0,0,0,0
SetToolBaudRate(115200)
Sleep(200)
ToolAnalogMode(0) --设置为485 模式
Sleep(200)
temp1 = 0x60
for i=1,2 do
	temp = i-1+temp
	GWrite(0x01,{temp})
	Sleep(500)
local ret = GRead(0x01)
Sleep(100)

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


	for i=1,4 do
		temp1 = 0x60
		temp1 = i-1+temp1
			GWrite(0x01,{temp1,temp1,temp1,temp1,temp1,temp1,temp1,temp1})
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
	  GWrite(0x01,{temp1,temp1,temp1,temp1,temp1,temp1,temp1,temp1})
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
	Sleep(200)
aim_current     = 15.0 --电流模式下测量的预期值，电流量程4~20ma
aim_voltage_10V = 5.0  --电压0~10V 模式下的预期电压值 5V 
aim_voltage_5V  = 5.0  --电压0~5V  模式下的预期电压值 5V 

Sleep(200)

GWrite(0x01,{0x65})
Sleep(200)
ToolAnalogMode(10)-- 电流测量模式
Sleep(200)
Current_1 = ToolAI(1) --  返回值为真实的电流值 单位mA,量程4~20mA
Current_2 = ToolAI(2) --  返回值为真实的电流值 单位mA 
current_bias_1 = math.abs(Current_1-aim_current)
current_bias_2 = math.abs(Current_2-aim_current)

if  current_bias_1<= 2 and current_bias_2 <= 2 then 
	print("4-20mA OK")
	Sleep(200)
else
	print("4-20mA NG")
end
print("current test done:\n")
print(string.format("通道1电流 = %f mA,偏差为%f mA",Current_1,current_bias_1))
print(string.format("通道2电流 = %f mA,偏差为%f mA",Current_2,current_bias_2))

Sleep(200)

ToolAnalogMode(11)
Sleep(200)
voltage_5_1 = ToolAI(1)
voltage_5_2 = ToolAI(2)
bias_V_5_1 = math.abs(voltage_5_1 - 5.0)
bias_V_5_2 = math.abs(voltage_5_2 - 5.0)

if bias_V_5_1 <= 0.1 and bias_V_5_2 <= 0.1 then 
	print("0-5V OK")	
else
	print("0-5V NG")
end
print("0~5V voltage test :\n")
print(string.format("通道1电压值：%f V,偏差值：%f V",voltage_5_1,bias_V_5_1))
print(string.format("通道2电压值：%f V,偏差值：%f V",voltage_5_2,bias_V_5_2))

Sleep(200)

ToolAnalogMode(12)
Sleep(200)
voltage_10_1 = ToolAI(1)
voltage_10_2 = ToolAI(2)
bias_V_10_1 = math.abs(voltage_10_1 - 5.0)
bias_V_10_2 = math.abs(voltage_10_2 - 5.0)

if bias_V_10_1 <= 0.2 and bias_V_10_2 <= 0.2 then 
	print("0-10V OK")	
else
	print("0-10V NG")
end
print("0~10V voltage test :\n")
print(string.format("通道1电压值：%f V,偏差值：%f V",voltage_5_1,bias_V_5_1))
print(string.format("通道2电压值：%f V,偏差值：%f V",voltage_5_2,bias_V_5_2))
print("all done !")
while true do 
	Sleep(1000)
end