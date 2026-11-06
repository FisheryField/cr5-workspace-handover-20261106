
function split(str,reps )
    local resultStrList = {}
    string.gsub(str,'[^'..reps..']+',function ( w )
        table.insert(resultStrList,w)
    end)
    return resultStrList
end
n = 0
file = io.open("C:\\Users\\Administrator\\Desktop\\debug\\qpack.txt" ,"r");
for line in file:lines() do
	local result = split(line, " ")
	n = n + 1
	SetExicitCmd(result[1], result[2],result[3],result[4],result[5],result[6])
	--print(result[6])
end
file:close()
