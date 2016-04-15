function store_packages
	# the last variable is the store -- where to store to
	# the one before -- is the sources directory
	# others are packages
	if [ (count $argv) -lt 3 ]
		echo "Usage: store_packages pcg_name [pcg_names] source_dir store_dir"
	else
		set store_path $argv[-1]
		set source_path $argv[-2]
		set packages $argv[1..-3]
		if [ ! -e $store_path ];  echo "The provided store path does not exist: $store_path"; return 1; end
		if [ ! -e $source_path ]; echo "The provided source path does not exist: $source_path"; return 1; end
		echo "installing:" $packages
		echo "      from:" $source_path
		echo "        to:" $store_path
		echo "..........:"
		for p in $packages
			set package_source $source_path/$p
			if [ ! -e $package_source ]
				echo $package_source does not exist
				# how does fish script return with exit status?
				return 1
			else
				set package_hash (find $package_source -type f -exec md5sum "{}" \; | cut -f1 -d" " | sort | md5sum | cut -f1 -d" ")
				set stored_name "$p","$package_hash"
				echo "        as:" $stored_name
				if [ -e $store_path/$stored_name ]
					echo "Skipping, the package is found in the store."
				else
					echo "Running:"
					echo "cp -R $package_source $store_path/$stored_name"
					cp -R $package_source $store_path/$stored_name
				end
			end
		end
	end
end
