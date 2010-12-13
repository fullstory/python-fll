"""
This is the fll.aptlib module, it provides a class for preparing and using
apt in a chroot.

Authour:   Kel Modderman
Copyright: Copyright (C) 2010 Kel Modderman <kel@otaku42.de>
License:   GPL-2
"""

from contextlib import nested

import apt.cache
import apt.package
import apt_pkg
import datetime
import os
import shutil
import subprocess
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
    def __init__(self, chroot):
        self.chroot = chroot
        self.cache = None

    def init(self, preferences={}):
        """Initialise apt in the chroot."""
        self.cache = apt.cache.Cache(rootdir=self.chroot.path)

        # Set user configurable preferences.
        for pref in preferences:
            apt_pkg.config.set(pref, preferences[pref])

        # Must explicitly set architecture for interacting with chroot of
        # differing architecture to host. Chroot before invoking dpkg.
        apt_pkg.config.set('APT::Architecture', self.chroot.arch)
        apt_pkg.config.set('Dpkg::Chroot-Directory', self.chroot.path)

        # Avoid apt-listchanges / dpkg-preconfigure
        apt_pkg.Config.clear("DPkg::Pre-Install-Pkgs")

    def sources_list(self, sources, cached_uris=False, src_uris=False):
        """Write apt sources to file(s) in /etc/apt/sources.list.d/*.list.
        Create /etc/apt/sources.list with some boilerplate text about
        the lists in /etc/apt/sources.list.d/."""
        def write_sources_list_comment(filename, lines, mode='w'):
            try:
                with open(filename, mode) as fh:
                    if mode == 'a':
                        print >>fh, '\n'
                    for n in range(30):
                        print >>fh, '# '
                    print >>fh, '#\n'
                    for line in lines:
                        print >>fh, '# %-58s#\n' % line
                    for n in range(30):
                        print >>fh, '# '
                    print >>fh, '#\n'
            except IOError, e:
                raise AptLibError('failed to modify sources.list: ' + e)

        sources_list = self.chroot.chroot_path('/etc/apt/sources.list')
        lines = ['Please use /etc/apt/sources.list.d/ instead of this file',
                 'and create a separate *.list configuration file for each',
                 'repository, containing the type, URI, desired suites and',
                 'components for that repository.', '',
                 'See sources.list(5) for information. Only http, ftp or',
                 'file URIs can be used in apt source lists. CD-ROMs are',
                 'managed via the apt-cdrom utility.']
        write_sources_list_comment(sources_list, lines)

        for name, source in sources.items():
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
                
                try:
                    with open(self.chroot.chroot_path(fname), 'a') as fh:
                        print >>fh, 'deb ' + line
                        if src_uris:
                            print >>fh, 'deb-src ' + line
                except IOError, e:
                    raise AptLibError('failed to write %s: %s' % (fname, e))

    def _gpg(self, args):
        """Fetch gpg public keys and save to apt's trusted keyring."""
        gpg = ['gpg', '--batch', '--no-options', '--no-default-keyring',
               '--secret-keyring', '/etc/apt/secring.gpg',
               '--trustdb-name', '/etc/apt/trustdb.gpg',
               '--keyring', '/etc/apt/trusted.gpg']
        gpg.extend(args)
        self.chroot.cmd(gpg)

    def key(self, sources, keyserver='wwwkeys.eu.pgp.net'):
        """Import and gpg keys, install any -keyring packages that are
        required to authenticate apt sources. Update and refresh apt cache."""
        gpgkeys = list()
        keyrings = list()

        for name, source in sources.items():
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
            recv_keys.insert(1, keyserver)
            recv_keys.insert(2, '--recv-keys')
            self._gpg(recv_keys)

        if fetch_keys:
            fetch_keys.insert(0, '--fetch-keys')
            self._gpg(fetch_keys)

        if keyrings:
            self.install(keyrings)

    def commit(self):
        self.chroot.mountvirtfs()
        self.cache.commit(fetch_progress=AptLibProgress())
        self.chroot.umountvirtfs()
        self.cache.open()

    def update(self):
        self.cache.update(fetch_progress=AptLibProgress())
        self.cache.open()

    def dist_upgrade(self, commit=True):
        self.cache.upgrade(dist_upgrade=True)
        if commit:
            self.commit()

    def install(self, packages, commit=True):
        #with self.cache.actiongroup(): # segfaults
        for p in packages:
            self.cache[p].mark_install()

        print 'INSTALL %d packages - %sB download - %sB required' % \
            (self.cache.install_count,
             apt_pkg.size_to_str(self.cache.required_download),
             apt_pkg.size_to_str(self.cache.required_space))

        if commit:
            self.commit()

    def purge(self, packages, commit=True):
        #with self.cache.actiongroup(): # segfaults
        for p in packages:
            self.cache[p].mark_delete(purge=True)
        if commit:
            self.commit()

    def installed(self):
        for p in sorted(self.cache.keys()):
            if self.cache[p].is_installed:
                yield self.cache[p]


class AptLibProgress(apt.progress.base.AcquireProgress):
    """Progress report for apt."""
    _time = None

    def fail(self, item):
        if item.owner.status == item.owner.STAT_DONE:
            line = 'IGN ' + item.description
        else:
            line = 'ERR %s [%s]' % (item.description, item.owner.error_text)
        print line

    def ims_hit(self, item):
        line = 'HIT ' + item.description
        if item.owner.filesize:
            line += ' [%sB]' % apt_pkg.size_to_str(item.owner.filesize)
        print line

    def fetch(self, item):
        line = 'GET ' + item.description
        if item.owner.filesize:
            line += ' [%sB]' % apt_pkg.size_to_str(item.owner.filesize)
        print line

    def start(self):
        self._time = datetime.datetime.utcnow()

    def stop(self):
        duration = datetime.datetime.utcnow() - self._time

        if self.total_items == 0:
            return

        line = 'GOT %s items' % self.total_items
        if duration.seconds >= 60:
            line += ' in %dm:%02ds' % divmod(duration.seconds, 60)
        else:
            line += ' in %d.%ds' % (duration.seconds, duration.microseconds)
        line += ' [%sB]' % apt_pkg.size_to_str(self.total_bytes)
        print line
