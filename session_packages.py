"""
The module with a bunch of functions implementing packaging for Python.
"""

import os
from os.path import isdir, isfile, normpath, basename
from shutil import copytree
import hashlib


def hashfile(afile, hasher, blocksize=65536):
    # FIXME: using hash of binary -- it will differ on different machines?
    buf = afile.read(blocksize)
    while len(buf) > 0:
        hasher.update(buf)
        buf = afile.read(blocksize)
    return hasher.digest()

def checksum_directory_content(directory):
    """checksum_directory_content(directory)

    basicaly runs
    find $directory -type f -exec md5sum "{}" \; | cut -f1 -d" " | sort | md5sum | cut -f1 -d" "

    Gets sha256 hashes of binary content of all not-hidden files
    within the directory and all sub-directories.
    Returns the string of the hash of sorted sequence of file hashes,
    where each byte is in hex.
    """

    all_hashes = []
    all_nothidden_files = []
    for d, dirs, files in os.walk(directory):
        files = [f for f in files if not f[0] == '.']
        dirs[:] = [d for d in dirs if not d[0] == '.']
        # all_nothidden_files += [d + '/' + f for f in files]
        all_hashes += [(f, hashfile(open(d + '/' + f, 'rb'), hashlib.sha256())) for f in files]

    # all_hashes = [(f, hashfile(open(f, 'rb'), hashlib.sha256())) for f in all_nothidden_files]

    sorted_hash = hashlib.sha256()
    for fname, h in sorted(all_hashes, key=lambda i: i[1]):
        print(fname, ''.join([hex(b)[2:] for b in h]))
        sorted_hash.update(h)

    return ''.join([hex(b)[2:] for b in sorted_hash.digest()])

def packagename_selectors(package_name):
    """package_checksum_selector(checksum)
    """

    def name_selector(package_directory):
        """name_selector(package_directory)

        returns True if package_directory name == %s
        """ % package_name
        return basename(normpath(package_directory)) == package_name

    return name_selector

def package_checksum_selectors(checksum):
    """package_checksum_selector(checksum)
    """

    def the_checksum_selector(package_directory):
        """the_checksum_selector(package_directory)

        returns True if checksum of package_directory content equals %s
        """ % checksum
        return checksum_directory_content(package_directory) == checksum

    return the_checksum_selector

'''
def package_threedotversion_selectors(primary, secondary, last):
    """package_threedotversion_selectors(primary, secondary, last)
    """

    def the_checksum_selector(package_directory):
        """the_checksum_selector(package_directory)

        returns True if checksum of package_directory content equals %s
        """ % checksum
        return checksum_directory_content(package_directory) == checksum

    return the_checksum_selector
'''

'''
ready_package -- a directory
    the name of the directory = name of the package
    the first line of the file `version` in the dircetory = version
    the lines of the file deps.list in the directory = (package_spec) names of dependancies

package_spec -- a tuple of <name>, <version>, <checksum>
    or the corresponding string "<name>,<version>,<checksum>"

package_selector -- a function,
    takes the package_spec parameters,
    returns True or False if the package passes requirements
'''


def package_spec(pckg_path):
    """package_spec(pckg_path)

    pckg_path -- full path to the directory of the package
    version -- the first line of `version` file in the dir
    checksum -- checksum of the contents

    returns name_of_the_dir, version, checksum
    """

    version = None
    if isfile(pckg_path + '/version'):
        with open(pckg_path + '/version', 'r') as f:
            version = f.readline().strip().replace(' ', '_')
    return basename(normpath(pckg_path)), version, checksum_directory_content(pckg_path)

def store_packages(packages_requested, sources, storage_directory):
    """store_packages(packages_requested, sources, storage_directory)

    packages_requested -- list of tuples <name>, <package_selector>
    sources -- list of directories containing ready-package dirs named as package <name>
    storage_directory -- name/full path of the directory to store to

    The ready package may also contain `version` and `deps.list` files.

    Name from package_spec is searched for in all sources.
    The found packages are selected upon checksumed and copied in storage_directory
    as <name>,<version>,<hash> -- if <version> is not available 'None' is used.
    """

    # packages_to_store contains
    #  full path to ready package dir
    #  and the full storage name
    packages_to_store = {}

    # TODO: sources and packages/package_specs should be separate convenient objects here
    #       so that one can do `package_name in source` check etc
    for package_name, selector in packages_requested:
        # package_name in source -> get_package_spec(source, package_name)
        # if passes the selector -- done
        candidates = [s + '/' + package_name for s in sources if isdir(s + '/' + package_name)]
        # TODO: should I unfold to full path here?

        # Go through candidate fullpathes and select the first package passing the selector 
        selected = None
        for c in candidates:
            spec = package_spec(c)
            if selector(spec):
                selected = c, spec
                break

        if not selected:
            raise Exception("The package %s is not found in %s" % (package_name, sources))

        # then selected == candidate_fullpath, package_spec
        # Now check if the selected package is really new
        # -- none of the already selected variants of the same package pass the selector
        # continue to next package otherwise
        same_pckgs_selected = packages_to_store.get(package_name)
        if same_pckgs_selected and any(selector(spec) for _, spec in same_pckgs_selected):
            continue
        packages_to_store.setdefault(package_name, []).append(selected)

    for _, variants in packages_to_store.items():
        for package_path, spec in variants:
            # cp -R package_path storage_directory/"{},{},{}".format(*spec)
            copytree(package_path, storage_directory + "/{},{},{}".format(*spec))

    




def linkup_env_dir(env_dir, storage_dir, packages):
    pass


