#!/usr/bin/fish


function err
	echo $argv >&2
end



#set needed (readelf -d $elf | grep NEEDED)
#set soname (readelf -d $elf | grep SONAME | cut -d "[" -f2 | cut -d "]" -f1)
#set the_hash ( shasum $elf | cut -f1 -d" " )

function needed
	readelf -d $argv[1]  | grep NEEDED | cut -f2 -d"[" | cut -f1 -d"]"
end

function find_assembled_files
	#find $assembly_store -mindepth 1 -maxdepth 2 -name "$argv[1]" -type f
	find . -mindepth 1 -maxdepth 2 -name "$argv[1]" -type f
end

function find_stored_files
	find -L $file_store -maxdepth 1 -name "$argv[1],*" -type f # -exec basename "{}" \;
end

function assemble
	# input - file-definition (now -- name), file_store & assembled_store
	# return relative path from assembled store to the assembled file (file_dir/file or ./file_dir/file)
	set file_name $argv[1]
	err assembling $file_name
	#set file_store $argv[2]
	#set assembled_store $ergv[3]

	set file_assembled (find_assembled_files $file_name)
	if [ $file_assembled ]
		err the file is found assembled
		echo $file_assembled[1]
		exit 0
	end
	# if file is not assembled -- get it from the store, make dir, cp file there, assemble NEEDED in libs/ dir
	err file was not assembled before, getting it from file-store

	set files_stored (find_stored_files $file_name)
	if [ ! $files_stored ]
		err not found such names in $file_store
		exit 1
	end

	set target_file $files_stored[1]
	set libs (needed $target_file)
	err chose target file $target_file
	set target_name (echo (basename $target_file) | sed 's/\([^,]\),.*/\1/')
	err $target_name

	set target_dir_final (basename $target_file)","
	set target_dir (basename $target_file)",temp"
	mkdir -p $target_dir/libs/
	cp $target_file $target_dir/$target_name

	if [ $libs ]
		#mkdir $target_dir/libs/
		for dep in $libs
			err dependency: $dep
			#assemble $dep in the assembled store
			set assembled_dep_path (assemble $dep)
			err assembled: $assembled_dep_path

			if [ $assembled_dep_path ]
				#
				cd $target_dir/libs
				ln -s ../../$assembled_dep_path .
				#cd - # this is not allowed?
				cd ../../
				# could make pre-defined link with -T:
				# ln -s -T ../lib/path.so target/libs/libname.so
			else
				err failed to assemble $dep
				err setting target dir to failed
				set failed 1
			end
		end
	end

	if [ $failed ]
		set target_dir_final $target_dir_final,failed
	end
	#touch $target_dir/$target_name
	mv $target_dir $target_dir_final
	touch $target_dir_final/$target_name
	echo $target_dir_final/$target_name
end


set elf_name $argv[1]
set file_store (realpath $argv[2])
set assembly_store (realpath $argv[3])

err $elf_name
err $file_store
err $assembly_store

set initial_pwd (pwd)
cd $assembly_store
echo $assembly_store/(assemble $elf_name)
cd $initial_pwd # return back from the assembled store


