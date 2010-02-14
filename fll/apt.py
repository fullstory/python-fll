"""
This is the fll.apt module, it provides a class for preparing and using
apt in a chroot.

Authour:   Kel Modderman
Copyright: Copyright (C) 2010 Kel Modderman <kel@otaku42.de>
License:   GPL-2
"""

import os
import shutil


class AptError(Exception):
    """
    An Error class for use by Apt.
    """
    pass


class Apt(object):
    """
    A class for preparing and using apt within a chroot.

    Arguments:
    chroot - an fll.chroot.Chroot object
    """
    chroot = None

    def __init__(self, chroot):
        self.chroot = chroot

    def prep_apt_sources(self, sources, cached_uris=False):
        """Write apt sources to file(s) in /etc/apt/sources.list.d/*.list.
        Create /etc/apt/sources.list with some boilerplate text about
        the lists in /etc/apt/sources.list.d/.
        
        Arguments:
        sources - a dict structure containing repoistory data"""
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
                raise AptError('failed to modify sources.list: ' + e)
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
                
                fh = None
                try:
                    fh = open(self.chroot.chroot_path(fname), 'a')
                    print >>fh, 'deb ' + line
                    print >>fh, 'deb-src ' + line
                except IOError, e:
                    raise AptError('failed to write %s: %s' % (fname, e))
                finally:
                    if fh:
                        fh.close()

    def prep_apt_gpgkeys(self, sources):
        """Import and gpg keys, install any -keyring packages that are
        required to authenticate apt sources.
        
        Arguments:
        sources - a dict structure containing repoistory data"""
        gpgkeys = list()
        keyrings = list()

        for name, source in sources.items():
            gpgkey = source.get('gpgkey')
            if gpgkey:
                gpgkeys.append(gpgkey)
    
            keyring = source.get('keyring')
            if keyring:
                keyrings.append(keyring)

        for key in gpgkeys:
            if not os.path.isdir(self.chroot.chroot_path('/root/.gnupg')):
                os.mkdir(self.chroot.chroot_path('/root/.gnupg'))

            cmd = 'gpg --no-options '

            if os.path.isfile(key):
                dest = self.chroot.chroot_path('/tmp/' + os.path.basename(key))
                shutil.copy(key, dest)
                cmd += '--import /tmp/' + os.path.basename(key)
            elif key.startswith('http') or key.startswith('ftp'):
                cmd += '--fetch-keys ' + key
            else:
                cmd += '--keyserver wwwkeys.eu.pgp.net --recv-keys ' + key

            self.chroot.cmd(cmd)

        if gpgkeys:
            self.chroot.cmd('apt-key add /root/.gnupg/pubring.gpg')

        if keyrings:
            self.chroot.cmd('apt-get update')
            cmd = 'apt-get --allow-unauthenticated --yes install'.split()
            cmd.extend(keyrings)
            self.chroot.cmd(cmd)

        self.chroot.cmd('apt-get update')
