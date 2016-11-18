#!/usr/bin/fish

# take the path to the ELF binary
# with patchelf --set-rpath
# add RUNPATH="$ORIGIN/bin_name,bin_hash/:$ORIGIN/:$ORIGIN/common_libs"
# to the elf binary,
# if it contains NEEDED

# uses:
# file, readelf, patchelf
# basename

#echo $argv

set the_bin $argv[1]
#echo $the_bin

if file $the_bin | grep ELF > /dev/null
  echo is elf
  if readelf -d $the_bin | grep NEEDED > /dev/null
    echo setting the RUNPATH
    set bin_name (basename $the_bin)
    # -- need to add the hash to the directory of the binary
    #    but adding hash to the binary will change its' hash...
    # thus, for now calculate hash with RUNPATH=""
    patchelf --set-rpath "" $the_bin
    set bin_hash (shasum $the_bin | cut -f1 -d " ")
    patchelf --set-rpath "\$ORIGIN/$bin_name,$bin_hash/:\$ORIGIN/:\$ORIGIN/common_libs" $the_bin
  else
    echo doesnt have NEEDED
    exit 0
  end
else
  echo $the_bin is not elf binary
  exit 1
end

