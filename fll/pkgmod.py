"""
This is the fll.pkgmod module, it provides a class for parsing package
profile modules.

Author:    Kel Modderman
Copyright: Copyright (C) 2012 Kel Modderman <kel@otaku42.de>
License:   GPL-2
"""

import os

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
    def __init__(self, aptlib=None, architecture=None, config={}, locales={}):
        self.apt = aptlib
        self.arch = architecture
        self.config = config
        self.locales = locales
        self.pkgs = set()

        try:
            self.profile = config['name']
        except KeyError:
            self.profile = None

        try:
            self.modules = self.locate_modules(config['dir'])
        except KeyError:
            self.modules = {}

        self.pkgs.update(config['packages'])

    
    def locate_modules(self, dirname):
        modules = {}
        for p, d, f in os.walk(dirname):
            modules[f] = os.path.join(p, f)
        return modules
