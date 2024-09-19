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

import logging
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

def find_so(so, paths):
    for p in paths:
        if isfile(p + "/" + so):
            return p + "/" + so

    return None

def traverse_deps(filename, parent_nodes=set(), accumulated_dependencies={}):
    """traverse_deps(filename)

    Traverse the dependency tree of <filename>.
    And return the dependency graph as DepNode.
    """

    logging.debug(f'traverse_deps: {filename} {len(accumulated_dependencies)}')

    thebin = realpath(filename)
    name, directory = basename(thebin), dirname(thebin)

    # TODO: error-check here:
    try:
        elf_header = [l.decode() for l in check_output("readelf -d %s" % thebin, shell=True).split(b'\n')]

    except CalledProcessError as e:
        #print("FAILED TO READ ELF " + thebin)
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

    if name in accumulated_dependencies:
        # check if you can reuse the node
        existing_deps = accumulated_dependencies[name]

        # if the definition matches one of existing nodes, use it
        defs = [n.full_definition for n, _ in existing_deps]
        if full_definition in defs:
            ind = defs.index(full_definition)
            existing_deps[ind][1] += 1 # increase the reuse score in the graph

            matching_node = existing_deps[ind][0]
            matching_node.parents.update(parent_nodes)
            return matching_node

    dependencies = set()
    for dep in needed:
        # if it contains a slash -- look relative to binary's directory
        # otherwise in $LD_LIBRARY_PATH
        # RUNPATH
        # or defaults "/lib/" "/usr/lib/" "/lib/"(uname -m)"-linux-gnu/" "/usr/lib/"(uname -m)"-linux-gnu/"
        if '/' in dep:
            if isfile(directory + dep):
                dependencies.add(traverse_deps(directory + dep, parent_nodes, accumulated_dependencies))
            else:
                logging.error(f"FILE NOT FOUND: {directory + dep}")
                # and supposedly ld doesn't follow to other sorces of dependencies

        else:
            libenv_bin = find_so(dep, paths_ld_lib)
            if libenv_bin:
                dependencies.add(traverse_deps(libenv_bin, parent_nodes, accumulated_dependencies))
                continue

            #
            if runpath:
                runpath_bin = find_so(dep, runpath)
                if runpath_bin:
                    dependencies.add(traverse_deps(runpath_bin, parent_nodes, accumulated_dependencies))
                    continue

            stdlibs_bin = find_so(dep, paths_stdlibs)
            if stdlibs_bin:
                #print(stdlibs_bin)
                dependencies.add(traverse_deps(stdlibs_bin, parent_nodes, accumulated_dependencies))
                continue

            logging.error("DEP NOT FOUND %s" % dep)

    new_dep = DepNode(name, soname, full_definition, filename, runpath, dependencies, parent_nodes)

    # check for collisions with existing dependencies
    # accumulated_dependencies = {'filename': [[DepNode, score], ...]}
    if new_dep.name in accumulated_dependencies:
        existing_deps = accumulated_dependencies[new_dep.name]
        # check for conflicts and save multiple versions if needed
        if new_dep in existing_deps:
            # no conflict - this node can be satisfied by one of accumulated ones
            # increase the score of the node
            existing_deps[existing_deps.index[new_dep]][1] += 1

    else:
        accumulated_dependencies[new_dep.name] = [[new_dep, 1]]

    return new_dep

#print(sys.argv)
#target_name = sys.argv[1]

def targets_to_graph(targets):
    entry_graph_nodes = []
    accumulated_nodes = {}

    for targ in targets:
        full_filename = None
        if isfile(targ):
            #print("got file", targ)
            full_filename = targ

        else:
            try:
                #print("which %s" % targ)
                filename = check_output("which %s" % targ, shell=True).strip().decode()
                #print("got a command, found it at %s" % filename)
                full_filename = filename

            except CalledProcessError as e:
                print("usage: ./all_deps.py <cmd|filename>")
                raise Exception(f"Could not find the binary: which {targ}") from e

        parent_nodes = set()
        dep_graph = traverse_deps(full_filename, parent_nodes, accumulated_nodes)
        entry_graph_nodes.append(dep_graph)

    return entry_graph_nodes, accumulated_nodes

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

    parser.add_argument("target_names", nargs='+', help="the names of the binaries to parse for dependencies, filename or a name found in $PATH")
    parser.add_argument("-m", "--more", action='store_true',
                        help="print more: print the accumulated nodes and their scores")
    parser.add_argument("-d", "--debug", action='store_true', help="DEBUG logging")

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    #acc_deps  = {}
    #dep_graph = traverse_deps(full_filename, acc_deps)
    #for ch in dep_graph.children:
    #    print(f'{ch.name} {ch.children}')

    dep_graphs, acc_deps = targets_to_graph(args.target_names)

    for dep_graph in dep_graphs:
        for node_list in dep_graph.list_graph():
            print(' > '.join(str(n) for n in node_list))

    if args.more:
        for name, nodes in acc_deps.items():
            print(f'{name:20}:  {" ".join(f"[{score:2}] {n.full_definition}" for n, score in nodes)}')

