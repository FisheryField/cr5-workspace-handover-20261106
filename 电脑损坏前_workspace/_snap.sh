ls -l /home/ftp/PlcLogic/Recipe/SavePos.txt /home/ftp/PlcLogic/Recipe/SlaveInfos.SlaveInfos.txtrecipe
echo "---HEX---"
od -A d -t x1 /home/ftp/PlcLogic/Recipe/SavePos.txt | head -4
echo "---DATE---"
date
