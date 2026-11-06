local nnm = 0
local E=GetABZ()
for i=1,16 do
	num = 0
	DO(i,ON)
	Sleep(200)
	if DI(i+16) == 1 and DI(i) == 1 then  --判断DI17和DI1是否同时被至高
		num = num+1 
	end
	Sleep(200)
	DO(i,OFF)
	Sleep(200)
	if num == 1 and DI(i+16) == 0  and DI(i) == 0 then  --判断上个条件是否满足，以及DI17和DI1是否被至低
		Sleep(100)
		nnm=nnm+1
		--print("DO("..i.."):OK")
	else
		print("DO("..i.."):NG")  --判断条件，不满足打印NG
	end
	if nnm == 16 then  --判断条件，满足打印OK
	print("DO DI OK")
	Wait(2000)
	end
end


Sleep(500)
AO(1,0)			--将AO1输出为0
AO(2,0)			--将AO2输出为0
Sleep(1000)
num =0
for i = 1, 10 do 	
	local a = i*1.0		--模拟输出值依次叠加
	local b = a
	Sleep(800)
	AO(1,a)
	AO(2,a)
	Sleep(100)
	c=AI(1)			--定义变量AI1的值存放在c里面；在输出下方才生效
	d=AI(2)			--定义变量AI2的值存放在c里面；在输出下方才生效
	Sleep(800)
	print(string.format("i = %d , a:%f ,c = %f, d = %f",i,a,c,d))
	if math.abs(b-c) >=0.005 and math.abs(b-c) <= 0.25 then  --判断条件：输入AI1和AI2的值减去变量b取绝对值小于等于200
			if math.abs(b-d) >= 0.005 and math.abs(b-d)<=0.25 then 
				num=num+1
				--print("AO("..i..")=AI("..i..")  OK ")		
				Sleep(500)
			else 
				print("AO2("..i..")NG!!!")		--判断条件，不满足打印NG
			end
		else
			print("AO1("..i..")NG!!!")
		end		
	if num == 10 then  		--判断条件，满足打印OK
	print("AO AI OK")
	Sleep(500)
	--Wait(2000)
	end
end
AO(1,0)
AO(2,0)
Sleep(200)

DO(16,ON)
Sleep(200)
DO(16,OFF)
Sleep(200)
DO(16,ON)
Sleep(200)			
		if E > 1 then		--当ABZ的值大于0则OK 
	print("ABZ ok")
	Sleep(200)
	else 
	print("ABZ NG")
end 
DO(16,OFF)
Pause()

while true do 
	Sleep(1000)
end