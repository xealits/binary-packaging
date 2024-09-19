#!/usr/bin/python3
'''
preliminary functions to save binaries in the standard "binary store" format:

    store_dir/name/version/name,version,hash

    with RPATH=$ORIGIN/:$ORIGIN/name_deps/:$ORIGIN/common
'''

import argparse, logging
import textwrap
from subprocess import check_output, CalledProcessError
import os
from os import mkdir, makedirs
from os.path import basename, isdir, isfile, realpath
from shutil import copy2 #copyfile
import logging

from dep_node import DepNode, DepDefinition, str_to_def


def set_rpath(filename):
    name = basename(filename)
    rpath_def = f"$ORIGIN/{name}_deps/:$ORIGIN/:$ORIGIN/common/"
    command = f"patchelf --set-rpath '{rpath_def}' {filename}"
    output = check_output(command, shell=True).decode().strip()
    logging.debug(output)

def hash_file(filename):
    command = f'sha256sum {filename}'
    output = check_output(command, shell=True).decode().strip()
    logging.debug(output)

    hashtag = output.split()[0]
    return hashtag

def convert_to_store(dep_node, store_dir):
    assert isinstance(dep_node, DepNode)

    #assert isdir(store_dir)
    temp_dirname = store_dir + '/temp'
    makedirs(temp_dirname, exist_ok=True)

    #
    fullname = dep_node.value['full_path']
    assert basename(fullname) == dep_node.name
    tempfile = temp_dirname + '/' + dep_node.name
    #copyfile(fullname, tempfile)
    copy2(fullname, tempfile)

    # set the RPATH
    set_rpath(tempfile)

    # now make the hash
    hashtag = hash_file(tempfile)
    # TODO: check that this actual hashtag is not in conflict with the dependency?

    #
    name, version = dep_node.full_definition.filename, dep_node.full_definition.version
    store_path = f'{store_dir}/{name}/{version}/'
    store_file = f'{name},{version},{hashtag}'
    makedirs(store_path, exist_ok=True)
    #copyfile(tempfile, store_path + '/' + store_file)
    copy2(tempfile, store_path + '/' + store_file)

def find_dep(dependency_def, store_dir):
    assert isdir(store_dir)
    store_dir = realpath(store_dir)

    fname, version = dependency_def.filename, dependency_def.version
    dir_bins = store_dir + '/' + fname + '/' + version
    assert isdir(dir_bins)

    if len(dependency_def.hash) == 0:
        # then any file will work
        any_file = os.listdir(dir_bins)[0]
        return dir_bins + '/' + any_file

    #
    # find the first binary that passes the hash requirement
    for hsh in dependency_def.hash:
        file_bin = f'{fname},{version},{hsh}'
        full_path = dir_bins + '/' + file_bin
        if isfile(full_path):
            return full_path

    raise Exception(f"Could not find a dependency in store {store_dir}: {dependency_def}")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
            formatter_class = argparse.RawDescriptionHelpFormatter,
            description = textwrap.dedent("""Setup an environment from a store with patched binaries"""),
            epilog = textwrap.dedent("""
            Example:

            """)
            )

    parser.add_argument("env_file",  type=str, help="filename with the environment definitions")
    parser.add_argument("env_dir",   type=str, help="directory where to set up symlinks to binaries")
    parser.add_argument("store_dir", type=str, help="directory with the stored patched binaries")

    parser.add_argument("-d", "--debug", action='store_true', help="DEBUG logging")

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)


    dependency_defs = []
    with open(args.env_file) as f:
        for depstr in f.readlines():
            dependency_defs.append(str_to_def(depstr.strip()))
            # TODO nope, I need to build the dependency graph out of this
            #      and check the collisions
            # but let's just dump it in 1 dir for now

    #
    makedirs(args.env_dir, exist_ok=True)
    for dep in dependency_defs:
        full_path = find_dep(dep, args.store_dir)
        # symlink it in the args.env_dir
        os.symlink(full_path, args.env_dir + '/' + dep.filename)
