"""
This is the fll.aptlib module, it provides a class for preparing and using
apt in a chroot.

Author:    Kel Modderman
Copyright: Copyright (C) 2010 Kel Modderman <kel@otaku42.de>
License:   GPL-2
"""

from contextlib import nested
from tempfile import NamedTemporaryFile

import apt.cache
import apt.package
import apt_pkg
import datetime
import os
import shutil
import subprocess
import fll.misc


class AptLibError(Exception):
    """
    An Error class for use by AptLib.
    """
    pass


class AptLib(object):
    """
    A class for preparing and using apt within a chroot.

    Options  Type                Description
    --------------------------------------------------------------------------
    chroot - (fll.chroot.Chroot) fll.chroot.Chroot object
    config - (dict)              the 'apt' section of fll.config.Config object
    """
    def __init__(self, chroot=None, config={}):
        if chroot is None:
            raise AptLibError('must specify chroot=')
        if not config:
            raise AptLibError('must specify config=')

        self.chroot = chroot
        self.config = config
        self.cache = None
        self._progress = AptLibProgress(quiet=config['quiet'])

        self.sources_list(final_uri=False, src=config['src'])
        self._init_cache()
        self.update()
        self.key(disable=config['key']['disable'])

    def _init_cache(self):
        """Initialise apt in the chroot."""
        print 'APT %s APT_PKG %s' % (apt_pkg.VERSION, apt_pkg.LIB_VERSION)
        # Must explicitly set architecture for interacting with chroot of
        # differing architecture to host. Chroot before invoking dpkg.
        apt_pkg.config.set('APT::Architecture', self.chroot.architecture)
        apt_pkg.config.set('Dpkg::Chroot-Directory', self.chroot.rootdir)

        self.cache = apt.cache.Cache(rootdir=self.chroot.rootdir)

        # Set user configurable preferences.
        for keyword, value in self.config['conf'].iteritems():
            apt_pkg.config.set(keyword, value)

        # Avoid apt-listchanges / dpkg-preconfigure
        apt_pkg.config.clear("DPkg::Pre-Install-Pkgs")

        # Debug apt preferences configuration
        #apt_pkg.config.set('Debug::pkgDPkgPM', 'true')
        fll.misc.debug(self.config['debug'], 'apt_pkg.config',
                       apt_pkg.config.dump())

    def deinit(self):
        self.sources_list(final_uri=True, src=False)
        #self.clean()

    def sources_list(self, final_uri=False, src=False):
        """Write apt sources to file(s) in /etc/apt/sources.list.d/*.list.
        Create /etc/apt/sources.list with some boilerplate text about
        the lists in /etc/apt/sources.list.d/."""
        def write_sources_list_comment(filename, lines, mode='w'):
            try:
                with open(filename, mode) as fh:
                    if mode == 'a':
                        print >>fh, '\n'
                    print >>fh, '%s#' % ('# '*30)
                    for line in lines:
                        print >>fh, '# %-58s#' % line
                    print >>fh, '%s#' % ('# '*30)
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

        for name, source in self.config['sources'].iteritems():
            description = source.get('description')
            if final_uri and source.get('final_uri'):
                uri = source.get('final_uri')
            else:
                uri = source.get('uri')
            suites = source.get('suites')
            components = source.get('components')

            fname = '/etc/apt/sources.list.d/%s.list' % name
            write_sources_list_comment(sources_list, [description, fname],
                                       mode='a')
            
            for suite in suites:
                line = '%s %s %s' % (uri, suite, ' '.join(components))
                try:
                    with open(self.chroot.chroot_path(fname), 'w') as fh:
                        print >>fh, 'deb ' + line
                        if src:
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

    def key(self, disable=False):
        """Import and gpg keys, install any -keyring packages that are
        required to authenticate apt sources. Update and refresh apt cache."""
        if disable is True:
            return

        gpgkeys = []
        keyrings = []

        for name, source in self.config['sources'].iteritems():
            gpgkey = source.get('gpgkey')
            if gpgkey:
                gpgkeys.append(gpgkey)
    
            keyring = source.get('keyring')
            if keyring:
                keyrings.append(keyring)

        fetch_keys = []
        recv_keys = []

        for key in gpgkeys:
            if os.path.isfile(key):
                with nested(NamedTemporaryFile(dir=self.chroot.rootdir),
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
            recv_keys.insert(1, self.config['key']['server'])
            recv_keys.insert(2, '--recv-keys')
            self._gpg(recv_keys)

        if fetch_keys:
            fetch_keys.insert(0, '--fetch-keys')
            self._gpg(fetch_keys)

        if keyrings:
            self.install(keyrings)

        if keyrings or fetch_keys or recv_keys:
            self.update()

    def commit(self):
        print 'APT COMMIT INSTALL %d DELETE %d GET %sB REQ %sB' % \
            (self.cache.install_count,
             self.cache.delete_count,
             apt_pkg.size_to_str(self.cache.required_download),
             apt_pkg.size_to_str(self.cache.required_space))

        mounted = self.chroot.mountvirtfs()
        try:
            self.cache.commit(fetch_progress=self._progress)
        except apt.cache.FetchFailedException, e:
            raise AptLibError('apt failed to fetch required archives')
        except SystemError, e:
            raise AptLibError('apt encountered an error: %s' % e)
        finally:
            if mounted > 0:
                self.chroot.umountvirtfs()

        self.open()

    def update(self):
        print 'APT UPDATE'
        try:
            self.cache.update(fetch_progress=self._progress)
        except apt.cache.FetchFailedException, e:
            raise AptLibError('apt failed to fetch required archives')
        self.open()

    def open(self):
        print 'APT CACHE'
        self.cache.open()

    def dist_upgrade(self, commit=True):
        self.cache.upgrade(dist_upgrade=True)

        if commit:
            self.commit()

    def install(self, packages, commit=True):
        #with self.cache.actiongroup(): # segfaults
        for p in packages:
            self.cache[p].mark_install()

        if commit:
            self.commit()

    def purge(self, packages, commit=True):
        #with self.cache.actiongroup(): # segfaults
        for p in packages:
            self.cache[p].mark_delete(purge=True)
        if commit:
            self.commit()

    def changes(self):
        for pkg in self.cache.get_changes():
            yield pkg

    def installed(self):
        for pkg in self.cache:
            if pkg.is_installed:
                yield pkg


class AptLibProgress(apt.progress.base.AcquireProgress):
    """Progress report for apt."""
    def __init__(self, quiet=False):
        apt.progress.base.AcquireProgress.__init__(self)
        self._quiet = quiet
        self._time = None

    def fail(self, item):
        apt.progress.base.AcquireProgress.fail(self, item)
        if item.owner.status == item.owner.STAT_DONE:
            line = 'APT IGN ' + item.description
        else:
            line = 'APT ERR ' + item.description
            if item.owner.error_text:
                line += ' [%s]' % item.owner.error_text
        if self._quiet is False:
            print line

    def ims_hit(self, item):
        apt.progress.base.AcquireProgress.ims_hit(self, item)
        line = 'APT HIT ' + item.description
        if item.owner.filesize:
            line += ' [%sB]' % apt_pkg.size_to_str(item.owner.filesize)
        if self._quiet is False:
            print line

    def fetch(self, item):
        apt.progress.base.AcquireProgress.fetch(self, item)
        line = 'APT GET ' + item.description
        if item.owner.filesize:
            line += ' [%sB]' % apt_pkg.size_to_str(item.owner.filesize)
        if self._quiet is False:
            print line

    def start(self):
        apt.progress.base.AcquireProgress.start(self)
        self._time = datetime.datetime.utcnow()

    def stop(self):
        apt.progress.base.AcquireProgress.stop(self)
        duration = datetime.datetime.utcnow() - self._time

        if self.total_items == 0:
            return

        line = 'APT GOT %s items' % self.total_items
        if duration.seconds >= 60:
            line += ' in %dm:%02ds' % divmod(duration.seconds, 60)
        else:
            line += ' in %d.%ds' % (duration.seconds, duration.microseconds)
        line += ' [%sB]' % apt_pkg.size_to_str(self.total_bytes)
        print line
