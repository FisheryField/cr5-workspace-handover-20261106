for d in /mToolServer/overTurn /home/ftp/PlcLogic/Recipe /home/ftp/.dobotConfig; do echo "=== $d ==="; ls -la $d 2>/dev/null; done
echo
echo "=== /mToolServer/overTurn/SavePos.txt (hex) ==="
xxd /mToolServer/overTurn/SavePos.txt 2>/dev/null || od -An -tx1z /mToolServer/overTurn/SavePos.txt
echo "=== /mToolServer/overTurn/SaveAxesValue.AxesValues.txtrecipe ==="
cat /mToolServer/overTurn/SaveAxesValue.AxesValues.txtrecipe
echo "=== /home/ftp/PlcLogic/Recipe/SavePos.txt (hex) ==="
xxd /home/ftp/PlcLogic/Recipe/SavePos.txt 2>/dev/null
echo "=== /home/ftp/PlcLogic/Recipe/SaveAxesValue.AxesValues.txtrecipe ==="
cat /home/ftp/PlcLogic/Recipe/SaveAxesValue.AxesValues.txtrecipe 2>/dev/null; ls -la /home/ftp/PlcLogic/Recipe/
echo "=== /home/ftp/PlcLogic/Recipe/Update.txt ==="
cat /home/ftp/PlcLogic/Recipe/Update.txt
echo "=== StartCnt ==="
cat /home/ftp/.dobotConfig/StartCnt
echo "=== mToolServer.log 尾部 ==="
tail -20 /mToolServer/mToolServer.log 2>/dev/null