# Binary packaging

A couple Python scripts for simple manual content-based packaging of ELF files.

```
$ ./all_deps.py -s temp/store1/ ls dir
$ ./all_deps.py -n ls dir > deps_example.txt
$ ./store_files.py deps_example.txt temp/env1 temp/store1/
```

I am just figuring out what's really needed. Hence no tests.
It seems like it operates on 3 things: a graph with nodes for binaries, of different versions and hashtags,
connected by their dependencies; a dictionary with the environment rules, i.e. spec
with the versions of dependencies for binaries (an ELF binary specifies only the NEEDED name);
and a simple dictionary with accumulated binaries, when an environment or a binary store
are being constructed.

The general idea is to try the following:

* it needs to keep track of the dependency graphs for a bunch of ELF executables
  where the nodes are all the executables and all their dependency files
  + for the graph, I will just use a class like `OptNode` from [`curses_menu`](https://github.com/xealits/curses_menu),
    then later it might need a real graph library (unfortunately dependency graphs tend to be big)

* if there are no collisions, all binaries can be dumped into 1 "dependency soup"
  directory, and they get a `RPATH=$ORIGIN/`
  + the dependency soup is just resolved by the linker while launching the binaries

* if there are 2 different versions of the same _executable_, then you need 2
  separate directories in `PATH`; the same if you just want to have a subset of executables
* to reuse the libraries without creating a ton of symlinks, use some convention
  like `RPATH=$ORIGIN/common`

* the tough case is when there is a collision in the libraries
  for the executable or another library, i.e. if there is a requirement for two
  different versions of some node (not executable) in the full dependency graph,
  then that node has to be pulled out of the "soup" directory with another `RPATH`
  convention like `RPATH=$ORIGIN/libfoo_deps/` and the special version of the node
  goes into this directory `./libfoo_deps/`

* the precise node versions are defined as `name,version,hashtag` with the hashtag
  of an actual dependency file
* the dependency requirements can span ranges of versions, lists of hashtags, etc

* it should work with symlinks to some flat store of the files: the linker gets
  `$ORIGIN` from the symlink location, not what it points to
  + so there are some "store" directories with just prepared binary files
  + and the environment directories on `PATH` just contain symlinks to the binaries
  + there can be many "store" directories, at user and system level, with names like
    `store1/bin_name/bin_version/name,version,hashtag.so` etc

To convert a bunch of existing binaries:

* pull their full dependency graph with `ldd` or whatever
* patch their `RPATH` with [`patchelf`](https://github.com/NixOS/patchelf) from NixOS
* copy to a "store" directory

Also to figure out the dependency on the `ld-linux` interpreter.
It is just another dependency here.

This tool is not intended as a serious packaging system.
The idea is to be able to copy paste a bunch of files onto a computer and run them,
with some headroom for less trivial situations.

# Notes

On the env rules file from `store_files.py`:

At this point, there is a list of dependencies from a file,
and there is the store directory - you can `readelf -d` the binaries there
to get the _names_ of their dependencies, without the version and hashtag.

What should be there is some way to specify the version and hashtags
that must be used for the dependencies of some binaries.
If it is not specified, then grab any file of the latest version of
the binary.

So, the file specifies the binaries that you want to get in the environment,
and additional rules for dependencies.

The additional rules specify the dependency of some binary. I.e. the binary
itself says only the name of the dependency, which is the interface name.
But the rule should also specify that _for this binary_ this dependency name
must come with some version or just some hashtag.

Then, how it works when I extend the environment with some other versions?
The new directory will come first in the PATH, and it will have common/ point
to the old directory. The other versions compose a new set of rules.
These rules can be compared with the old rules, whether they agree. If not,
then the new directory is like a graph extension for version conflicts?
The idea was that the PATH directories are for different executables.
Different directories is like graph deviations for version conflicts in
executables. But some dependencies can be shared.

The easiest would be to just symlink _all_ dependencies in the new PATH
directories.

Then, there could be sharing too: you probably have to traverse
the directories down the common/ symlinks (which are supposed to be on PATH),
looking for your dependency. I.e. for these new binaries, you update the rules,
overwritting the old rules when needed. Then you check the common/ first,
if a rule is not fullfilled, check the store and bring the new version
to the new PATH directory.

The rules do not have to nest, don't they? I.e. each rules is concerned only
with the dependencies of the given file.

Executable foo depends on libbar.so, which depends on libbaz.so. The rules
specify one dependency level at a time:

```
foo,ver,hashes > libbar.so,,hash
libbar.so,,hash > libbaz.so,,hash
qwe,, > libbar.so,ver,
```

It will need to find files by the hashes in the names, and by the versions.
Just use wildcards without / for the versions?

