
--local J6just={joint={0,0,0,0,0,0}}
--local J6lose={joint={0,0,0,0,0,30}}
function split(str,reps )
    local resultStrList = {}
    string.gsub(str,'[^'..reps..']+',function ( w )
        table.insert(resultStrList,w)
    end)
    return resultStrList
end

local zero={joint={0,0,0,0,0,0}}
MoveJ(zero)

setExcitMode(33)
file = io.open("/dobot/userdata/project/project/debug_6/qpack6.txt" ,"r");
for line in file:lines() do
	local result = split(line, " ")
	
	SetExicitCmd(result[1], result[2],result[3],result[4],result[5],result[6],result[7], result[8],result[9],result[10],result[11],result[12],result[13], result[14],result[15],result[16],result[17],result[18])
end
file:close()
DO(1,ON,"SYNC=1")

setExcitMode(3)
Sleep(1000)
DO(1,OFF,"SYNC=1")


