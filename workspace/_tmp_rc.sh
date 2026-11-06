#!/bin/sh
D=/home/ftp/PlcLogic/Recipe
echo '=== SaveAxesValue ==='
cat $D/SaveAxesValue.AxesValues.txtrecipe
echo
echo '=== SavePos.txt ==='
cat $D/SavePos.txt
echo
echo '=== SlaveInfos ==='
cat $D/SlaveInfos.SlaveInfos.txtrecipe
echo
echo '=== Update.txt ==='
cat $D/Update.txt
echo
echo '=== other recipe-ish files ==='
ls -la $D
echo '=== END ==='
