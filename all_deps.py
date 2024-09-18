#!/usr/bin/python3

"""
The module defines traverse_deps and supproting functions
for traversing ELF file dependancy tree.

Used:
`readelf -d` utility for reading the dynamic section of ELF files,
`uname -m` for getting the <platform> of the machine.

Dependencies are searched according to ld.so man page:

    1. by the dependency's name in NEEDED field,
       if it contains a slash `/`

    2. if not, it searches through:
       1) paths in `LD_LIBRARY_PATH` environment variable,
       2) `RUNPATH` of the ELF's dynamic section
       3) in standard paths:
           /lib/, /usr/lib/, /lib/<platform>-linux-gnu/, /usr/lib/<platform>-linux-gnu/
          --- where <platform> is found from `uname -m`.

"""

import argparse
import textwrap

import sys
from os import environ
from os.path import isfile, realpath, basename, dirname
from subprocess import check_output, CalledProcessError

from dep_node import DepNode, DepDefinition

MAX_DEPTH = 10
#only_binaries=False

platform = check_output("uname -m", shell=True).decode().strip()
# has got to be a better way
#print(platform)
paths_stdlibs = ['/lib/', '/lib64/', "/lib/"+ platform +"-linux-gnu/", '/usr/lib/', "/usr/lib/"+ platform +"-linux-gnu/"]
#print(paths_stdlibs)

paths_ld_lib = []
if 'LD_LIBRARY_PATH' in environ:
    paths_ld_lib = environ["LD_LIBRARY_PATH"].split(':')[1:]
# example:
#>>> os.environ["LD_LIBRARY_PATH"]
#':/opt/AMDAPP/lib/x86_64:/opt/AMDAPP/lib/x86'

parsed_files = {}

def find_so(so, paths):
    for p in paths:
        if isfile(p + "/" + so):
            return p + "/" + so

    return None

def s(depth):
    return ''.join(' ' if i % 2 == 0 else '|' for i in range(depth))

def traverse_deps(depth, filename, only_binaries=False):
    """traverse_deps(depth, filename, only_binaries=False)

    Traverse the dependency tree of <filename>.
    Output the tree in ASCII-art.
    Or print filenames of all dependencies per line,
    if only_binaries == True.
    """

    if depth == MAX_DEPTH:
        print("MAXIMUM DEPTH OF  %s  HAS BEEN REACHED" % MAX_DEPTH)

    thebin = realpath(filename)
    name, directory = basename(thebin), dirname(thebin)

    if thebin in parsed_files:
        #print(s(depth) + name, thebin, "SEEN ABOVE")
        #return 0
        # TODO no, only test for conflicts
        pass

    # TODO: error-check here:
    try:
        elf_header = [l.decode() for l in check_output("readelf -d %s" % thebin, shell=True).split(b'\n')]

    except CalledProcessError as e:
        #print(s(depth) + "FAILED TO READ ELF " + thebin)
        raise Exception(f'failed to readelf -d {thebin}') from e
    #print(elf_header)

    needed  = []
    runpath = []
    soname  = ""
    for line in elf_header:
        if "NEEDED" in line:
            needed.append( line.split('[')[1].split(']')[0] )
        elif "SONAME" in line:
            soname = line.split('[')[1].split(']')[0]
        elif "RUNPATH" in line:
            runpath = line.split('[')[1].split(']')[0].replace('$ORIGIN', directory).split(':')

    #
    # Full definition of this dependency node
    hashes = frozenset()
    full_definition = DepDefinition(name, soname, hashes)

    #if only_binaries:
    #    print(thebin)
    #else:
    #    print(s(depth) + name, thebin, "[%s]" %soname)
    #    print(s(depth) + "needed:", needed)
    #    print(s(depth) + "runpath:", runpath)

    parsed_files[thebin] = {'soname': soname, 'needed': needed, 'runpath': runpath}

    dependencies = set()
    for dep in needed:
        # if it contains a slash -- look relative to binary's directory
        # otherwise in $LD_LIBRARY_PATH
        # RUNPATH
        # or defaults "/lib/" "/usr/lib/" "/lib/"(uname -m)"-linux-gnu/" "/usr/lib/"(uname -m)"-linux-gnu/"
        if '/' in dep:
            if isfile(directory + dep):
                dependencies.add(traverse_deps(depth+1, directory + dep, only_binaries))
            else:
                print(s(depth) + f"FILE NOT FOUND: {directory + dep}")
                # and supposedly ld doesn't follow to other sorces of dependencies

        else:
            libenv_bin = find_so(dep, paths_ld_lib)
            if libenv_bin:
                dependencies.add(traverse_deps(depth+1, libenv_bin, only_binaries))
                continue

            #
            if runpath:
                runpath_bin = find_so(dep, runpath)
                if runpath_bin:
                    dependencies.add(traverse_deps(depth+1, runpath_bin, only_binaries))
                    continue

            stdlibs_bin = find_so(dep, paths_stdlibs)
            if stdlibs_bin:
                #print(stdlibs_bin)
                dependencies.add(traverse_deps(depth+1, stdlibs_bin, only_binaries))
                continue

            print(s(depth) + "DEP NOT FOUND %s" % dep)

    return DepNode(name, soname, full_definition, filename, runpath, dependencies)

#print(sys.argv)
#target_name = sys.argv[1]

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
            formatter_class = argparse.RawDescriptionHelpFormatter,
            description = textwrap.dedent("""
            Traverse dependancy tree of an ELF file using `readelf -d`.
            Output the full tree or aspects of it."""),
            epilog = textwrap.dedent("""
            Example:

            $ ./all_deps.py ls
            ls
            ls > libselinux.so.1
            ls > libselinux.so.1 > ld-linux-x86-64.so.2
            ls > libselinux.so.1 > libpcre2-8.so.0.11.2
            ls > libselinux.so.1 > libpcre2-8.so.0.11.2 > libc.so.6
            ls > libselinux.so.1 > libpcre2-8.so.0.11.2 > libc.so.6 > ld-linux-x86-64.so.2
            ls > libselinux.so.1 > libc.so.6
            ls > libselinux.so.1 > libc.so.6 > ld-linux-x86-64.so.2
            ls > libc.so.6
            ls > libc.so.6 > ld-linux-x86-64.so.2
            """)
            )

    parser.add_argument("target_name", help="the name of the binary to parse for dependencies, filename or a name found in $PATH")
    parser.add_argument("-b", "--binaries",  help="output only the full filenames of all dependencies",
                        action="store_true")

    args = parser.parse_args()
    #print(args.target_name)
    #print(args.binaries)
    #if args.binaries:
        #only_binaries = True
    #print(type(args.target_name))

    full_filename = None
    if isfile(args.target_name):
        #print("got file", args.target_name)
        full_filename = args.target_name

    else:
        try:
            #print("which %s" % args.target_name)
            filename = check_output("which %s" % args.target_name, shell=True).strip().decode()
            #print("got a command, found it at %s" % filename)
            full_filename = filename

        except CalledProcessError:
            print("couldn't parse the argument")
            print("usage: ./all_deps.py <cmd|filename>")

    dep_graph = traverse_deps(0, full_filename, args.binaries)
    for node_list in dep_graph.list_graph():
        print(' > '.join(str(n) for n in node_list))

