echo "对象              J6(slave8,3.1.5.0)   J1(slave3,3.2.D.8)"
printf "%-16s %-22s %s\n" "地址" "J6" "J1"
try() {
  a=$(/tmp/ecat_zero rv 8 $1 $2 2>&1 | tail -1 | sed 's/.*= //')
  b=$(/tmp/ecat_zero rv 3 $1 $2 2>&1 | tail -1 | sed 's/.*= //')
  printf "%-16s %-22s %s\n" "$1:$2" "${a:-FAIL}" "${b:-FAIL}"
}
try 0x2001 18
try 0x2001 20
try 0x2001 21
try 0x2008 1
try 0x2008 13
try 0x2008 29
try 0x200C 3
try 0x2001 19
try 0x2000 1
try 0x2000 23
