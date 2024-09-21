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
from collections import UserDict

from dep_node import DepNode, DepDefinition, str_to_def
from all_deps import readelf_dynamic, add_to_accumulated_nodes, check_in_accumulated_nodes


class BinaryDefFile(UserDict):
    def __getitem__(self, binary_def):
        '''
         __getitem__(self, binary_def)

        Find a definition in the dictionary that satisfies binary_def.
        I.e. the name is the same, the versions overlap, the hash tags overlap.
        '''

        assert isinstance(binary_def, DepDefinition)
        # self.data.keys() = list of DepDefinition
        for rule_def, rule in self.data.items():
            if rule_def.no_conflict(binary_def):
                return rule

        raise KeyError(f'Could not find a suitable definition for: {binary_def}')

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

def storefile_to_def(bin_path) -> DepDefinition:
    '''
    storefile_to_def(bin_path)

    DepDefinition of a concrete file in a store:
    name,version,hash
    '''

    full_definition = str_to_def(basename(bin_path))
    # there is exactly 1 hashtag in DepDefinition of a concrete file
    assert len(full_definition.hashes) == 1
    # TODO: there should be a way to confirm that the version is also specified

    return full_definition

def find_dep(bindef, store_dir, dep_rules={}, parent_nodes=set(), accumulated_binaries={}):
    '''
    find_dep(bindef, store_dir, dep_rules={}, accumulated_binaries={}):

    it recursively updates accumulated_binaries dictionary
    (which is similar to accumulated_binaries in the all_deps.py)
    it is a dictionary of {bin_name: [[DepNode, score] ...]}
    where DepNode are the binaries in the store directory
    '''

    assert isinstance(parent_nodes, set)
    assert isdir(store_dir)
    store_dir = realpath(store_dir)

    fname, version = bindef.filename, bindef.version
    dir_fname = store_dir + '/' + fname
    assert isdir(dir_fname), dir_fname

    #
    # if version is empty - match any
    if version == '':
        version = os.listdir(dir_fname)[0]

    dir_bins = dir_fname + '/' + version
    assert isdir(dir_bins), dir_bins

    #
    # check if this definition was already found
    matching_bin = check_in_accumulated_nodes(bindef, accumulated_binaries)
    if matching_bin is not None:
        matching_bin.parents.update(parent_nodes)
        # just return -- no need to search for dependencies
        # as they must be already found
        return #matching_bin

    #
    # otherwise, it is a new definition
    # find it in the store
    bin_path = None
    if len(bindef.hashes) == 0:
        # then any file will work
        any_file = os.listdir(dir_bins)[0]
        bin_path = dir_bins + '/' + any_file

    #
    # find the first binary that passes the hash requirement
    for hsh in bindef.hashes:
        file_bin = f'{fname},{version},{hsh}'
        full_path = dir_bins + '/' + file_bin

        if isfile(full_path):
            bin_path = full_path

        else:
            raise Exception(f"Could not find a file in store {store_dir}: {bindef}")

    #
    # now, there is a path to the binary: bin_path
    # it has some dependencies (readelf -d)
    # and some rules for them (dep_rules)
    # make the rules subset for the dependencies, and find them
    #
    full_definition = storefile_to_def(bin_path)
    needed, runpath, soname = readelf_dynamic(bin_path)

    dependencies = set()
    new_bin = DepNode(fname, soname, version, full_definition, bin_path, runpath, dependencies, parent_nodes)
    add_to_accumulated_nodes(new_bin, accumulated_binaries)

    #
    # find the dependencies in the store
    # and add them to accumulated_binaries
    #dep_rules_for_this_bin = dep_rules[fname]
    #dep_rules_for_this_bin = dep_rules[full_definition]
    # TODO this won't work! the definitions are hashed - they won't match loose versions etc!
    dep_rules_for_this_bin = dep_rules.get(full_definition, {})

    for dep_name in needed:

        if dep_name in dep_rules_for_this_bin:
            #def find_dep(bindef, store_dir, dep_rules={}, parent_nodes=set(), accumulated_binaries={}):
            #find_dep(bindef, args.store_dir, dep_rules, set(), accumulated_binaries)
            # TODO: this is the bit that gets complicated
            #       dependency rules is a dictionary for the whole environment, not just 1 binary
            #       it is {<bin_def>: {name: <def>, ...}}
            dep_def = dep_rules_for_this_bin[dep_name]

        else:
            dep_def = DepDefinition(dep_name, '', frozenset())

        find_dep(dep_def, store_dir, dep_rules, {new_bin}, accumulated_binaries)

def parse_env_file(env_file) -> dict:
    '''
    parse_env_file(env_file)

    returns a dictionary of {file_definition: {rules}}
    where rules is a dict of file definitions for dependencies:
    name: DepDefinition
    '''

    binary_defs = BinaryDefFile()

    # the file should probably be some YAML or TOML
    # I don't want JSON, because I want shortcuts for the user
    with open(env_file) as f:
        for defstr in f.readlines():
            # currently the definition string is
            # <binary definition> > <dependency def> <another> ...

            if '>' in defstr:
                bindef, dep_rules = defstr.split('>')
                bindef = str_to_def(bindef.strip())
                dep_rules_list = [str_to_def(rs) for rs in dep_rules.split()]
                dep_rules = {rule.filename: rule for rule in dep_rules_list}

            else:
                bindef = str_to_def(defstr.strip())
                dep_rules = {}

            binary_defs[bindef] = dep_rules
            # TODO nope, I need to build the dependency graph out of this
            #      and check the collisions
            # but let's just dump it in 1 dir for now

    return binary_defs

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
            formatter_class = argparse.RawDescriptionHelpFormatter,
            description = textwrap.dedent("""Setup an environment from a store with patched binaries"""),
            epilog = textwrap.dedent("""
            Example:
            ./store_files.py    env_example1.txt temp/env1 temp/store1/
            ./store_files.py -t env_example2.txt temp/env1 temp/store1/
            """)
            )

    parser.add_argument("env_file",  type=str, help="filename with the environment definitions")
    parser.add_argument("env_dir",   type=str, help="directory where to set up symlinks to binaries")
    parser.add_argument("store_dir", type=str, help="directory with the stored patched binaries")

    parser.add_argument("-t", "--test",  action='store_true', help="dry pass, just print symlink commands, don't execute them")
    parser.add_argument("-d", "--debug", action='store_true', help="DEBUG logging")

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    dependency_defs = parse_env_file(args.env_file)

    #
    makedirs(args.env_dir, exist_ok=True)
    accumulated_binaries = {}
    for bindef, dep_rules in dependency_defs.items():
        #full_path = find_dep(bindef, args.store_dir, dep_rules)
        find_dep(bindef, args.store_dir, dep_rules, set(), accumulated_binaries)

    for name, defs in accumulated_binaries.items():
        full_path = defs[0][0].value['full_path']

        # symlink it in the args.env_dir
        if args.test:
            print(f"os.symlink({full_path}, {args.env_dir} + '/' + {name})")

        else:
            os.symlink(full_path, args.env_dir + '/' + name)

