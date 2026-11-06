F=/dobot/userdata/project/settings/function/homeEncoder.json
echo "=== 文件状态 ==="
ls -la $F
echo
echo "=== 全部记录 (日期 时间 | innerEncoder[J1..J6]) ==="
tr -d ' \n' < $F | sed 's/},{/}\n{/g' | while read -r line; do
  enc=$(echo "$line" | sed -n 's/.*"innerEncoder":\[\([^]]*\)\].*/\1/p')
  t=$(echo "$line" | sed -n 's/.*"time":"\([^"]*\)".*/\1/p')
  d=$(echo "$line" | sed -n 's/.*"date":"\([^"]*\)".*/\1/p')
  hs=$(echo "$line" | sed -n 's/.*"jointHomeState":\[\([^]]*\)\].*/\1/p')
  echo "$d $t  [$enc]"
done
echo
echo "=== 文件里 J6(第6个) 的历史值 ==="
tr -d ' \n' < $F | sed 's/},{/}\n{/g' | while read -r line; do
  enc=$(echo "$line" | sed -n 's/.*"innerEncoder":\[\([^]]*\)\].*/\1/p')
  t=$(echo "$line" | sed -n 's/.*"time":"\([^"]*\)".*/\1/p')
  j6=$(echo "$enc" | cut -d, -f6)
  echo "  $t  J6=$j6"
done
