--WARNING!:Please keep enough room for the CR5 arm to move
local ip="192.168.5.1"  --Define the CR5 IP address
local port=6001 		--Define CR5 port number
local err=0				--Initializes the system to return information
local socket=0			--Initializes the connection object
err, socket = TCPCreate(true, ip, port)		--Create TCP network,"true" is the server,"false" is the client
if err == 0 then	--The judgment system returns information,"0"Net created successfully,"1" Failed to create network
err = TCPStart(socket, 0) --TCP wait connection
if err == 0 then
local RecBuf --Initializes the receive file
while true do
TCPWrite(socket, "Going") --Send "Going" to the connection destination
err, RecBuf = TCPRead(socket,0,"string") --Read the data sent by the connection target in character mode and save it to ReBuf
if err == 0 then
Go(P1,"SYNC=1") 
Go(P2,"SYNC=1")
print(buf)
else
print("Read error ".. err)
break
end
end
else
print("Create failed ".. err)
end
TCPDestroy(socket) --Shut down the TCP network
else
print("Create failed ".. err)
end
