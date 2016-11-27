#!/usr/bin/fish

#echo $argv[1]
set elf $argv[1]
set elf_name (basename $elf)

set needed (readelf -d $elf | grep NEEDED)
set soname (readelf -d $elf | grep SONAME | cut -d "[" -f2 | cut -d "]" -f1)
set the_hash ( shasum $elf | cut -f1 -d" " )


if [ $needed[1] ]
	# RUNPATH has to be set
	# plus, the dependency file should be generated

	# due to setting RUNPATH, the hash of the file is calculated with empty RUNPATH
	# and then the RUNPATH is set to standard string:
	# $ORIGIN/$elf:$ORIGIN/:$ORIGIN/libs/
	# -- surprisingly this method doesn't work
	# the hashes are random
	# it's logged in log1

	patchelf --set-rpath "\$ORIGIN/$elf_name,libs/:\$ORIGIN/:\$ORIGIN/libs/" $elf
	#mv $elf $elf,$the_hash
else
	# no need to set RUNPATH or generate dependencies.YANL, just hash the file
	#shasum $elf | cut -f1 -d" "
end

echo $the_hash

