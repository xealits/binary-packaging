#!/usr/bin/fish

#echo $argv[1]
set elf $argv[1]
#set elf_name (basename $elf)

readelf -d $elf  | grep NEEDED | cut -f2 -d"[" | cut -f1 -d"]"

