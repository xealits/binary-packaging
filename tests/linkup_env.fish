# FIXME: the different package versions are not considered,
# version collisions are not considered as well

function linkup_env
	# the last variable is the env -- where the env links are
	# the one before it is the store -- where the packages are stored
	# others are package names, i.e. the environment to setup
	if [ (count $argv) -lt 3 ]
		echo >&2 "Usage: linkup_env pcg_name [pcg_names] store_dir env_dir"
		return 2
	end

	set env_dir $argv[-1]
	set store_path $argv[-2]
	set packages $argv[1..-3]

	if [ -e $env_dir ]
	  echo >&2 "The provided environment path already exists: $env_dir"
	  return 1
	end
	if [ ! -e $store_path ]
	  echo >&2 "The provided store path does not exist: $source_path"
	  return 1
	end

	echo >&2 "linking-up:" $packages
	echo >&2 "      from:" $store_path
	echo >&2 "        to:" $env_dir
	echo >&2 "..........:"

	for p in $packages
		echo checking input package:
		# set stored_names $store_path/$p,*
		ls -d $store_path/$p,*

		if [ (count (ls -d $store_path/$p,*)) = 0 ]
			echo >&2 "Requested package not found:" $p
			return 1
		end
	end

	# so, the requested packages are stored
	# get the full environment from them:
	# all the packages, including dependancies

	set env_packages (get_package_env $store_path $packages)
	echo >&2 "Final env:" $env_packages
	mkdir $env_dir
	for package_name in $env_packages
	  echo $package_name
	  # getting the first package of the ones matching by the name:
	  set stored_package (ls -d $store_path/$package_name,*)[1]
	  echo >&2 "linking" $stored_package
	  # linking the package name into the env_dir
	  ln -s (realpath $stored_package[1]) $env_dir/$package_name
	end
end


function get_package_env
  if [ (count $argv) -lt 2 ]
    # echo >&2 "Usage: get_package_env pckg_store [packages_names]"
    # echo >&2 "the function supposes and ovewrites pckg_env_cur variable"
    return 0
  end

  # unpack the arguments:
  set store_path $argv[1]
  set packages $argv[2..-1]

  # the argument packages are supposed to exist in the store
  # check their dependancies (in deps.list files)
  # if some are not in the list and do exist in the store,
  # get_package_env on them returns them + their dependencies

  set dependencies

  for p in $packages
    set stored_ps (ls -d $store_path/$p,*)
    echo >&2 "Found " (count stored_ps) " stored packages corrsponding to" $p "(chose the first one)"
    # FIXME: here we rely on the first output of ls -- it will break
    set stored_ps $stored_ps[1]
    echo >&2 $stored_ps
    if [ -e "$stored_ps/deps.list" ]
      for d in (cat "$stored_ps/deps.list")
        # FIXME: in fact here we need to check the versions/hashes of dependancy and the packages list
        if contains $d $packages; continue; end
        if [ (count (ls $store_path/$p,*)) = 0 ]
          echo >&2 "Dependancy package $d is not stored in $store_path"
          return 1
        end
        set dependencies $dependencies $d
      end
    end
  end

  for p in $packages
    echo $p
  end
  for p in (get_package_env $store_path $dependencies)
    echo $p
  end
end
