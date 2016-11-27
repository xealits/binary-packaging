#!/usr/bin/fish

#echo $argv[1]
set elf $argv[1]
set elf_name (basename $elf)
set soname (readelf -d $elf | grep SONAME | cut -d "[" -f2 | cut -d "]" -f1)

# elf_name = name,,hash
# in the string substitute the name to soname


if [ $soname ]
	set solink (echo $elf_name | sed -r "s/^[^,]+/$soname/")
	# FIXME: the file has got to be in current directory!
	#echo $solink
	ln -s $elf $solink
end

