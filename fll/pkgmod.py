"""
This is the fll.pkgmod module, it provides a class for parsing package
profile modules.

Author:    Kel Modderman
Copyright: Copyright (C) 2012 Kel Modderman <kel@otaku42.de>
License:   GPL-2
"""

import fnmatch
import os

class PkgModError(Exception):
    """
    An Error class for use by Profile.
    """
    pass


class PkgMod(object):
    """
    A class for parsing package profile modules.

    Options        Type                Description
    --------------------------------------------------------------------------
    aptlib       - (fll.aptlib.AptLib) fll.aptlib.AptLib object
    architecture - (str)               Architecture codename
    config       - (dict)              The 'profile' section of a
                                       fll.config.Config object
    locales      - (dict)              dict of locales to be considered when
                                       selecting packages from apt's cache
    """
    def __init__(self, aptlib=None, architecture=None, config={}, locales={}):
        self.apt = aptlib
        self.arch = architecture
        self.config = config
        self.locales = locales
        self.pkgs = set()
        self.profiles = {}
        self.lists = {}
        self.debconf = {}
        self.postinst = {}

        try:
            self.locate_files(config['dir'])
        except KeyError:
            # this seems to be pointless?
            self.modules = {}

        try:
            self.profile = config['name']
        except KeyError:
            self.profile = None

        if self.profile != None and len(self.profiles.keys()) > 0:
            self.pkgs.update(self.expand_profile())

        try:
            self.pkgs.update(config['packages'])
        except KeyError:
            pass

    def locate_files(self, dirname):
        for path, dirs, files in os.walk(dirname):
            for d in dirs:
                if d.startswith('.'):
                    dirs.remove(d)
            
            for f in fnmatch.filter(files, '*.profile'):
                profile = f.rsplit('.', 1)[0]
                self.profiles[profile] = os.path.join(path, f)

            for f in fnmatch.filter(files, '*.list') + \
                     fnmatch.filter(files, '*.list.%s' % self.arch):
                print f
                self.lists[f] = os.path.join(path, f)

            for f in fnmatch.filter(files, '*.debconf'):
                self.debconf[f] = os.path.join(path, f)

            for f in fnmatch.filter(files, '*.postinst'):
                self.postinst[f] = os.path.join(path, f)

    def expand_profile(self):
        lists = []
        pkgs = []
        if self.profile in self.profiles:
            fname = self.profiles[self.profile]
        else:
            raise PkgModError('unknown package profile: %s' % self.profile)
        
        fh = None
        try:
            fh = open(fname, 'r')
            for line in fh.readlines():
                if not line.startswith('#include '):
                    continue
                for l in line.split()[1:]:
                    if l in self.lists:
                        print l
                        lists.append(self.lists[l])
                    else:
                        raise PkgModError('unknown package list: %s' % l)

                    arch_l = '%s.%s' % (l, self.arch)
                    if arch_l in self.lists:
                        lists.append(self.lists[arch_l])

                    # XXX: debconf + postinst
        except:
            pass
        finally:
            if fh:
                fh.close()

        for fname in lists:
            fh = None
            try:
                fh = open(fname, 'r')
                for line in fh.readlines():
                    if not line:
                        continue
                    pkgs.append(line.strip())
            except:
                pass
            finally:
                if fh:
                    fh.close()

        return pkgs
