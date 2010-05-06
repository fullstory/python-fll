"""
This is the fll.aptlib module, it provides a class for preparing and using
apt in a chroot.

Authour:   Kel Modderman
Copyright: Copyright (C) 2010 Kel Modderman <kel@otaku42.de>
License:   GPL-2
"""

from __future__ import with_statement
from contextlib import nested

import subprocess
import apt.cache
import apt.progress
import apt.package
import apt_pkg
import os
import shutil
import tempfile


class AptLibError(Exception):
    """
    An Error class for use by AptLib.
    """
    pass


class AptLib(object):
    """
    A class for preparing and using apt within a chroot.

    Arguments:
    chroot - (str) an fll.chroot.Chroot object
    """
    def __init__(self, chroot, sources, cached_uris=False, src_uris=False):
        self.chroot = chroot
        self.sources = sources

        self.prep_apt_sources(cached_uris=cached_uris, src_uris=src_uris)

        apt_pkg.init()
        # required for working on a chroot of differing architecture to host
        if self.chroot.arch:
            apt_pkg.config.set('APT::Architecture', self.chroot.arch)
        # dpkg executed within chroot
        apt_pkg.config.set('Dpkg::Chroot-Directory', self.chroot.path)
        # dpkg executed on host, using chroot admindir + instdir
        #apt_pkg.config.set('Dpkg::Options::', '--root=%s' % self.chroot.path)

        self.cache = self.prep_cache()

    def prep_cache(self):
        cache = apt.cache.Cache(progress=apt.progress.base.OpProgress(),
                                rootdir=self.chroot.path)

        # Avoid apt-listchanges / dpkg-preconfigure
        apt_pkg.Config.clear("DPkg::Pre-Install-Pkgs")

        return cache

    def prep_apt_sources(self, cached_uris=False, src_uris=False):
        """Write apt sources to file(s) in /etc/apt/sources.list.d/*.list.
        Create /etc/apt/sources.list with some boilerplate text about
        the lists in /etc/apt/sources.list.d/."""
        def write_sources_list_comment(filename, lines, mode='w'):
            fh = None
            try:
                fh = open(filename, mode)
                if mode == 'a':
                    fh.write('\n')
                for n in range(30):
                    fh.write('# ')
                fh.write('#\n')
                for line in lines:
                    fh.write('# %-58s#\n' % line)
                for n in range(30):
                    fh.write('# ')
                fh.write('#\n')
            except IOError, e:
                raise AptLibError('failed to modify sources.list: ' + e)
            finally:
                if fh:
                    fh.close()

        sources_list = self.chroot.chroot_path('/etc/apt/sources.list')
        lines = ['Please use /etc/apt/sources.list.d/ instead of this file',
                 'and create a separate *.list configuration file for each',
                 'repository, containing the type, URI, desired suites and',
                 'components for that repository.', '',
                 'See sources.list(5) for information. Only http, ftp or',
                 'file URIs can be used in apt source lists. CD-ROMs are',
                 'managed via the apt-cdrom utility.']
        write_sources_list_comment(sources_list, lines)

        for name, source in self.sources.items():
            description = source.get('description')
            uri = source.get('uri')
            cached_uri = source.get('cached_uri')
            suite = source.get('suite')
            components = source.get('components')

            fname = '/etc/apt/sources.list.d/%s.list' % name
            write_sources_list_comment(sources_list, [description, fname],
                                       mode='a')
            
            suites = suite.split()
            for suite in suites:
                if cached_uris and cached_uri:
                    line = '%s %s %s' % (cached_uri, suite, components)
                else:
                    line = '%s %s %s' % (uri, suite, components)
                
                fh = None
                try:
                    fh = open(self.chroot.chroot_path(fname), 'a')
                    print >>fh, 'deb ' + line
                    if src_uris:
                        print >>fh, 'deb-src ' + line
                except IOError, e:
                    raise AptLibError('failed to write %s: %s' % (fname, e))
                finally:
                    if fh:
                        fh.close()

    def _gpg(self, args):
        gpg = ['gpg', '--batch', '--no-options', '--no-default-keyring',
               '--secret-keyring', '/etc/apt/secring.gpg',
               '--trustdb-name', '/etc/apt/trustdb.gpg',
               '--keyring', '/etc/apt/trusted.gpg']
        gpg.extend(args)
        self.chroot.cmd(gpg)

    def prep_apt(self):
        """Import and gpg keys, install any -keyring packages that are
        required to authenticate apt sources. Update and refresh apt cache."""
        gpgkeys = list()
        keyrings = list()

        for name, source in self.sources.items():
            gpgkey = source.get('gpgkey')
            if gpgkey:
                gpgkeys.append(gpgkey)
    
            keyring = source.get('keyring')
            if keyring:
                keyrings.append(keyring)

        fetch_keys = list()
        recv_keys = list()

        for key in gpgkeys:
            if os.path.isfile(key):
                with nested(tempfile.NamedTemporaryFile(dir=self.chroot.path),
                            file(key)) as (fdst, fsrc):
                    shutil.copyfileobj(fsrc, fdst)
                    fdst.flush()
                    self._gpg(['--import',
                               self.chroot.chroot_path_rel(fdst.name)])
            elif len(key) == 8:
                recv_keys.append(key)
            else:
                fetch_keys.append(key)

        if recv_keys:
            recv_keys.insert(0, '--keyserver')
            recv_keys.insert(1, 'wwwkeys.eu.pgp.net')
            recv_keys.insert(2, '--recv-keys')
            self._gpg(recv_keys)

        if fetch_keys:
            fetch_keys.insert(0, '--fetch-keys')
            self._gpg(fetch_keys)

        if keyrings:
            self.update()
            self.install(keyrings)
        else:
            self.update()

    def _commit(self):
        self.cache.commit()
        self.cache.open(progress=apt.progress.base.OpProgress())

    def update(self):
        self.cache.update()
        self.cache.open(progress=apt.progress.base.OpProgress())

    def install(self, packages):
        #with self.cache.actiongroup(): # segfaults
        for p in packages:
            self.cache[p].mark_install()
        self._commit()

    def remove(self, packages):
        #with self.cache.actiongroup(): # segfaults
        for p in packages:
            self.cache[p].mark_delete(purge=True)
        self._commit()

    def installed(self):
        for p in sorted(self.cache.keys()):
            if self.cache[p].is_installed:
                yield self.cache[p]
        #return [self.cache[p] for p in sorted(self.cache.keys())
        #        if self.cache[p].is_installed]
