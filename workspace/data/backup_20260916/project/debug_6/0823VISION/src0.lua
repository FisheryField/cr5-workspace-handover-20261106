--[[
		P1 : 待机点
		P2 : 拍照点
		P3 : 取料过度点（相机发送）
		P4 : 取料点（相机发送）
		P5 : 放料过度点
		P6 : 放料点
		DO1 : 夹爪抓取
		DO2 : 夹爪释放

	变量：
		Capture : 柔性抓手正压反馈信号
		Drop : 柔性抓手负压反馈信号
--]]

--DI检测函数
function myDI(io)

	local t1 = DI(io)

	if t1 == 1 then
		Sleep(50)
		local t2 = DI(io)
		if t2 == 1 then
			return 1
		end
	end
	return 0

end

--夹爪抓取
function Capture()
	
	DO(2,0)
	DO(1,1)

	while true do 

		if myDI(Capture) == 1 then
			break
		else
			print("柔性抓手正压气压不够")
			Sleep(1000)
		end	

		Sleep(100)
	end	
	
end

--夹爪释放
function Dropt()

	DO(1,0)
	DO(2,1)

	while true do 

		if myDI(Dropt) == 1 then
			break
		else
			print("柔性抓手负压气压不够")
			Sleep(1000)
		end	

		Sleep(100)
	end	

end

--复位DO
function Reset()
	DO(1,0)
	DO(2,0)
end

--获取当前机器人坐标值并转换成字符串存储于K中
function pos()

	P = GetPose()
	print(P)
	G1=tostring(P.coordinate[1])
	G2=tostring(P.coordinate[2])
	G3=tostring(P.coordinate[3])
	G4=tostring(P.coordinate[4])
	G5=tostring(P.coordinate[5])
	G6=tostring(P.coordinate[6])			
	K = G1..","..G2..","..G3..","..G4..","..G5..","..G6

end

local ip="192.168.1.6"
local port=6001
local err=0
local socket=0
local PIG={}
local Capture = 1 -- 柔性抓手正压反馈信号接在机器人 DI1 端口
local Dropt = 2 -- 柔性抓手负压反馈信号接在机器人 DI2 端口


--[[

	主程序由此开始

--]]

Reset()
Go(P1)--待机点
err, socket = TCPCreate(true, ip, port)
Sleep(5)
if err == 0 then
    err = TCPStart(socket, 0)
	Sleep(1000)

    if err == 0 then

        while true do

        	print("等待拍照信号")
        	err,buf=TCPRead(socket,0,"string")

        	--机器人等待触发相机拍照的信号
        	while true do 

        		if buf.buf == "START" then
 					break
 				else
 					print("拍照信号应为START,请重发")
 					err,buf=TCPRead(socket,0,"string")
 				end	

 				Sleep(100)	
        	end	

        	--判断机器人当前位置是否在拍照区
        	P = GetPose()

        	if P.coordinate[1] == P2.coordinate[1] and P.coordinate[2] == P2.coordinate[2] and P.coordinate[3] == P2.coordinate[3] then
				pos()--获取当前机器人坐标值并转换成字符串存储于K中
        		TCPWrite(socket,K)--将机器人当前坐标发送给相机
        	else
        		Go(P2,"SYNC=1")
				pos()
        		TCPWrite(socket,K)
        	end	

        	--接收视觉反馈的点位
			PIG= TCPReadMultiVision(socket, 0) --视觉发送数据格式为： {x1,y1,z1,a1,b1,c1;x2,y2,z2,a2,b2,c2}
			
			P3.coordinate = PIG.coordinate0
			P4.coordinate = PIG.coordinate1

			while true do 

				if err == 0 then
					break			
				else
					print("Create failed")
				end

				Sleep(100)
			end

			--判断视觉反馈的数据是否有效
			if P3.coordinate[1] == 0 and P3.coordinate[2] == 0 and P3.coordinate[3] ==0 then
				print("kong")
				Wait(2000)
			else
				Go(P3)
				Capture()
				Move(P4,"SYNC=1")
				Wait(300)
				Go(P3)
				Go(P5)
				Go(P6,"SYNC=1")
				Wait(300)
				Dropt()
				Wait(300)
				Go(P5)
				Go(P1)
			end
        end
    else
        print("Create failed ".. err)
    end
    TCPDestroy(socket)
else
  print("Create failed ".. err)
end
