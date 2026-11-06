for sub in 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do
  a=$(/tmp/ecat_zero rv 8 0x2001 $sub 2>&1 | tail -1 | sed 's/.*= //')
  b=$(/tmp/ecat_zero rv 3 0x2001 $sub 2>&1 | tail -1 | sed 's/.*= //')
  printf "  H01.%-2s  0x2001:%-2s   J6=%-16s J1=%s\n" "$sub" "$sub" "${a:-?}" "${b:-?}"
done
