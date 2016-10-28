#!/usr/bin/python3

import sys
from os import environ
from os.path import isfile, realpath, basename, dirname
from subprocess import check_output, CalledProcessError


MAX_DEPTH = 10

platform = check_output("uname -m", shell=True).decode().strip()
# has got to be a better way
print(platform)
stdlibs = ['/lib/', '/usr/lib/', "/lib/"+ platform +"-linux-gnu/", "/usr/lib/"+ platform +"-linux-gnu/"]
print(stdlibs)

libenv = environ["LD_LIBRARY_PATH"].split(':')[1:]
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

def traverse_deps(depth, filename):
    if depth == MAX_DEPTH:
        print("MAXIMUM DEPTH OF  %s  HAS BEEN REACHED" % MAX_DEPTH)

    thebin = realpath(filename)
    name, directory = basename(thebin), dirname(thebin)

    if thebin in parsed_files:
        #print(s(depth) + name, thebin, "SEEN ABOVE")
        return 0

    # TODO: error-check here:
    try:
        elf_header = [l.decode() for l in check_output("readelf -d %s" % thebin, shell=True).split(b'\n')]
    except CalledProcessError:
        print(s(depth) + "FAILED TO READ ELF " + thebin)
        return 1
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

    print(s(depth) + name, thebin, "[%s]" %soname)
    print(s(depth) + "needed:", needed)
    print(s(depth) + "runpath:", runpath)

    parsed_files[thebin] = {'soname': soname, 'needed': needed, 'runpath': runpath}

    for dep in needed:
        # if it contains a slash -- look relative to binary's directory
        # otherwise in $LD_LIBRARY_PATH
        # RUNPATH
        # or defaults "/lib/" "/usr/lib/" "/lib/"(uname -m)"-linux-gnu/" "/usr/lib/"(uname -m)"-linux-gnu/"
        if '/' in dep:
            if isfile(directory + dep):
                traverse_deps(depth+1, directory + dep)
            else:
                print(s(depth) + "FILE NOT FOUND")
                # and supposedly ld doesn't follow to other sorces of dependencies
        else:
            libenv_bin = find_so(dep, libenv)
            if libenv_bin:
                traverse_deps(depth+1, libenv_bin)
                continue

            #
            if runpath:
                runpath_bin = find_so(dep, runpath)
                if runpath_bin:
                    traverse_deps(depth+1, runpath_bin)
                    continue

            stdlibs_bin = find_so(dep, stdlibs)
            if stdlibs_bin:
                #print(stdlibs_bin)
                traverse_deps(depth+1, stdlibs_bin)
                continue

            print(s(depth) + "DEP NOT FOUND %s" % dep)

            
    return 0

#print(sys.argv)
target_name = sys.argv[1]

if isfile(target_name):
    print("got file", target_name)
    traverse_deps(0, target_name)
else:
    try:
        print("which %s" % target_name)
        filename = check_output("which %s" % target_name, shell=True).strip().decode()
        print("got a command, found it at %s" % filename)
    except CalledProcessError:
        print("couldn't parse the argument")
        print("usage: ./all_deps.py <cmd|filename>")
    traverse_deps(0, filename)

