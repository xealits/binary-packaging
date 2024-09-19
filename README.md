# Binary packaging

The project is a bunch of scripts for simple manual content-based packaging of ELF files.

Restarting this handy little project in 2024 with this plan to try out:

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

```
./all_deps.py -m ls dir
ls
ls > libc.so.6
ls > libc.so.6 > ld-linux-x86-64.so.2
ls > libselinux.so.1
ls > libselinux.so.1 > ld-linux-x86-64.so.2
ls > libselinux.so.1 > libc.so.6
ls > libselinux.so.1 > libc.so.6 > ld-linux-x86-64.so.2
ls > libselinux.so.1 > libpcre2-8.so.0.11.2
ls > libselinux.so.1 > libpcre2-8.so.0.11.2 > libc.so.6
ls > libselinux.so.1 > libpcre2-8.so.0.11.2 > libc.so.6 > ld-linux-x86-64.so.2
dir
dir > libc.so.6
dir > libc.so.6 > ld-linux-x86-64.so.2
dir > libselinux.so.1
dir > libselinux.so.1 > ld-linux-x86-64.so.2
dir > libselinux.so.1 > libc.so.6
dir > libselinux.so.1 > libc.so.6 > ld-linux-x86-64.so.2
dir > libselinux.so.1 > libpcre2-8.so.0.11.2
dir > libselinux.so.1 > libpcre2-8.so.0.11.2 > libc.so.6
dir > libselinux.so.1 > libpcre2-8.so.0.11.2 > libc.so.6 > ld-linux-x86-64.so.2
ld-linux-x86-64.so.2:  [ 2] DepDefinition(filename='ld-linux-x86-64.so.2', version='ld-linux-x86-64.so.2', hash=frozenset())
libc.so.6           :  [ 4] DepDefinition(filename='libc.so.6', version='libc.so.6', hash=frozenset())
libpcre2-8.so.0.11.2:  [ 1] DepDefinition(filename='libpcre2-8.so.0.11.2', version='libpcre2-8.so.0', hash=frozenset())
libselinux.so.1     :  [ 2] DepDefinition(filename='libselinux.so.1', version='libselinux.so.1', hash=frozenset())
ls                  :  [ 1] DepDefinition(filename='ls', version='', hash=frozenset())
dir                 :  [ 1] DepDefinition(filename='dir', version='', hash=frozenset())
```
