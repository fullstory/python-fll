"""
This is the fll.util module, it provides a few utility functions.

Authour:   Kel Modderman
Copyright: Copyright (C) 2008 Kel Modderman <kel@otaku42.de>
License:   GPL-2
"""


import os
import stat


def isexecutable(name):
    """
    Return True is file is executable, False otherwise.
    """
    try:
        mode = os.stat(name)[stat.ST_MODE]
    except OSError:
        return False

    if stat.S_ISREG(mode) and mode & stat.S_IXUSR:
        return True
    else:
        return False


def which(name):
    """
    Look in PATH for an executable `name'.
    """
    if os.path.isabs(name):
        if isexecutable(name):
            return name
        else:
            name = os.path.basename(name)

    for path in os.environ['PATH'].split(os.pathsep):
        filename = os.path.join(path, name)
        if isexecutable(filename):
            return filename

    return None


def lines_to_list(self, lines):
    """
    Return a list of whitespace stripped lines from a group of lines,
    ignoring lines which start with a comment.
    """
    return [line.strip() for line in lines.splitlines()
            if line.strip() and not s.lstrip().startswith('#')]


def prepare_dir(dir, uid = os.getuid(), gid = os.getgid()):
    """
    Create a directory, if it doesn't exist, and chown it according
    to the uid/gid arguments given. Return the real path to the directory.

    An OSError will be raised should anything fail here.
    """
    if not os.path.isdir(dir):
        os.makedirs(dir)
        os.chown(dir, uid, gid)
    return os.path.realpath(dir)
