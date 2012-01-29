"""
This is the fll.pkgmod module, it provides a class for parsing package
profile modules.

Author:    Kel Modderman
Copyright: Copyright (C) 2012 Kel Modderman <kel@otaku42.de>
License:   GPL-2
"""

class PkgModError(Exception):
    """
    An Error class for use by Profile.
    """
    pass


class PkgMod(object):
    """
    A class for parsing package profile modules.

    Options   Type                Description
    --------------------------------------------------------------------------
    profdir - (str)               path to directory containing package profile
                                  modules
    profile - (str)               the name of the package profile to parse
    aptlib  - (fll.aptlib.AptLib) fll.aptlib.AptLib object
    config  - (dict)              the 'profile' section of fll.config.Config
                                  object
    """
    def __init__(self, profdir=None, profile=None, aptlib=None, config={}):
        pass
