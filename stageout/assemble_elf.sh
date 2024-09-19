#!/usr/bin/fish




#set needed (readelf -d $elf | grep NEEDED)
#set soname (readelf -d $elf | grep SONAME | cut -d "[" -f2 | cut -d "]" -f1)
#set the_hash ( shasum $elf | cut -f1 -d" " )

set elf_name $argv[1]
set -x file_store (realpath $argv[2])
set -x assembly_store (realpath $argv[3])

function ASSEMBLY_FUNC
    /home/alex/Documents/projects/programs/local-pypckg-manager/assemble_func.sh $argv[1]
end

echo $elf_name >&2
echo $file_store >&2
echo $assembly_store >&2

set initial_pwd (pwd)
cd $assembly_store
#echo $assembly_store/(assemble $elf_name)
echo $assembly_store/(ASSEMBLY_FUNC $elf_name)
cd $initial_pwd # return back from the assembled store


