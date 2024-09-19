'''
preliminary functions to save binaries in the standard "binary store" format:

    store_dir/name/version/name,version,hash

    with RPATH=$ORIGIN/:$ORIGIN/name_deps/:$ORIGIN/common
'''

from subprocess import check_output, CalledProcessError
from os import mkdir, makedirs
from os.path import basename, isdir
from shutil import copyfile
import logging

from dep_node import DepNode


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
    copyfile(fullname, tempfile)

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
    copyfile(tempfile, store_path + '/' + store_file)

