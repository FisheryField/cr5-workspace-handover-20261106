echo "=== 控制器上的编译器 ==="
for c in gcc cc g++ arm-linux-gcc arm-none-linux-gnueabi-gcc clang tcc; do
  p=$(which $c 2>/dev/null); [ -n "$p" ] && echo "  $c -> $p"
done
echo "(空=没有)"
echo
echo "=== /usr/bin 前 60 个 ==="
ls /usr/bin 2>/dev/null | head -60
echo
echo "=== python/perl 有没有 ==="
for c in python python2 python3 perl awk; do p=$(which $c 2>/dev/null); [ -n "$p" ] && echo "  $c -> $p"; done
echo
echo "=== 内核版本 / 架构 ==="
uname -a
cat /proc/cpuinfo | grep -aE "model name|Processor|Features" | head -3
