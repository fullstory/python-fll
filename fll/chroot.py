"""
This is the fll.chroot module, it provides a class for bootstrapping
and executing commands within a chroot.

Authour:   Kel Modderman
Copyright: Copyright (C) 2010 Kel Modderman <kel@otaku42.de>
License:   GPL-2
"""

import os
import subprocess
import shutil


class FllChrootError(Exception):
    """
    An Error class for use by FllChroot.
    """
    pass


class FllChroot(object):
    """
    A class which provides the ability to bootstrap and execute commands
    within a chroot.

    Arguments:
    path     - path to root of chroot
    hostname - hostname of chroot
    """
    path = None
    hostname = None
    env = {'LANGUAGE': 'C', 'LC_ALL': 'C', 'LANG' : 'C', 'HOME': '/root',
           'PATH': '/usr/sbin:/usr/bin:/sbin:/bin', 'SHELL': '/bin/bash',
           'DEBIAN_FRONTEND': 'noninteractive', 'DEBIAN_PRIORITY': 'critical',
           'DEBCONF_NOWARNINGS': 'yes'}
    diverts = ['/usr/sbin/policy-rc.d', '/sbin/modprobe', '/sbin/insmod',
               '/usr/sbin/update-grub', '/usr/sbin/update-initramfs']

    def __init__(self, path, hostname='chroot'):
        self.path = path
        self.hostname = hostname

    def bootstrap(self, bootstrapper='cdebootstrap', suite='sid',
                  flavour='minimal', variant='minbase',
                  arch=None, mirror=None, quiet=False, verbose=False,
                  debug=False, include=list(), exclude=list()):

        """Bootstrap a Debian chroot. By default it will bootstrap a minimal
        sid chroot with cdebootstrap."""

        cmd = list()
        cmd.append(bootstrapper)

        if verbose:
            cmd.append('--verbose')

        if bootstrapper == 'cdebootstrap':
            if quiet:
                cmd.append('--quiet')
            elif debug:
                cmd.append('--debug')

            cmd.append('--flavour=' + flavour)
        elif bootstrapper == 'debootstrap':
            cmd.append('--variant=' + variant)
        else:
            raise FllChrootError('unknown bootstrapper: ' + bootstrapper)

        if arch:
            cmd.append('--arch=' + arch)

        if include:
            cmd.append('--include=' + (',').join(include))

        if exclude:
            cmd.append('--exclude=' + (',').join(exclude))
        
        cmd.append(suite)
        cmd.append(self.path)

        if mirror:
            cmd.append(mirror)
        else:
            raise FllChrootError('bootstrap() requires a mirror')

        print ' '.join(cmd)

        try:
            retv = subprocess.call(cmd)
        except:
            raise FllChrootError('unexpected error executing: ' + ' '.join(cmd))

        if retv != 0:
            raise FllChrootError('bootstrap() cmd failed: ' + ' '.join(cmd))

        # Some flavours use cdebootstrap-helper-rc.d, some don't. We'll
        # impliment our our own policy-rc.d for consistency.
        if bootstrapper == 'cdebootstrap':
            self.cmd('dpkg --purge cdebootstrap-helper-rc.d'.split())

    def prep_chroot(self):
        """Configure the basics to get a functioning chroot."""
        for fname in ('/etc/hosts', '/etc/resolv.conf'):
            os.unlink(self.chroot_fname(fname))
            shutil.copy(fname, self.chroot_fname(fname))

        for fname in ('/etc/fstab', '/etc/hostname', '/etc/kernel-img.conf',
                      '/etc/network/interfaces'):
            self.create_fname(fname)

        for fname in self.diverts:
            cmd = 'dpkg-divert --add --local --divert ' + fname + '.REAL'
            cmd += ' --rename ' + fname
            self.cmd(cmd)

            if fname == '/usr/sbin/policy-rc.d':
                self.create_fname(fname, mode=0755)
            else:
                os.symlink('/bin/true', self.chroot_fname(fname))

    def prep_apt_sources(self, sources, cached_uris=False, update=False):
        """Write apt sources to file(s) in /etc/apt/sources.list.d/*.list."""
        if os.path.isfile(self.chroot_fname('/etc/apt/sources.list')):
            os.unlink(self.chroot_fname('/etc/apt/sources.list'))

        gpgkeys = list()
        keyrings = list()

        for name, source in sources.items():
            description = source.get('description')
            uri = source.get('uri')
            cached_uri = source.get('cached_uri')
            suite = source.get('suite')
            components = source.get('components')
            
            gpgkey = source.get('gpgkey')
            if gpgkey:
                gpgkeys.append(gpgkey)
    
            keyring = source.get('keyring')
            if keyring:
                keyrings.append(keyring)

            if cached_uris and cached_uri:
                line = '%s %s %s' % (cached_uri, suite, components)
            else:
                line = '%s %s %s' % (uri, suite, components)

            fname = self.chroot_fname('/etc/apt/sources.list.d/%s.list' % name)
            
            fh = None
            try:
                fh = open(fname, 'w')
                print >>fh, '# ' + description
                print >>fh, 'deb ' + line
                print >>fh, 'deb-src ' + line
            except IOError, e:
                raise FllChrootError('failed to write apt sources.list: ' + e)
            finally:
                if fh:
                    fh.close()

        if not update:
            return

        for key in gpgkeys:
            if not os.path.isdir(self.chroot_fname('/root/.gnupg')):
                os.mkdir(self.chroot_fname('/root/.gnupg'))

            cmd = 'gpg --no-options '

            if os.path.isfile(key):
                dest = self.chroot_fname('/tmp/' + os.path.basename(key))
                shutil.copy(key, dest)
                cmd += '--import /tmp/' + os.path.basename(key)
            elif key.startswith('http') or key.startswith('ftp'):
                cmd += '--fetch-keys ' + key
            else:
                cmd += '--keyserver wwwkeys.eu.pgp.net --recv-keys ' + key

            self.cmd(cmd)

        if gpgkeys:
            self.cmd('apt-key add /root/.gnupg/pubring.gpg')

        if keyrings:
            self.cmd('apt-get update')
            cmd = 'apt-get --allow-unauthenticated --yes install'.split()
            cmd.extend(keyrings)
            self.cmd(cmd)

        self.cmd('apt-get update')
                
    def post_chroot(self):
        """Undo any changes in the chroot which should be undone. Make any
        final configurations."""
        for fname in ('/etc/hosts', '/etc/motd.tail', '/etc/resolv.conf'):
            # /etc/resolv.conf (and possibly others) may be a symlink to an 
            # absolute path - so do not clobber the host's configuration.
            if os.path.islink(self.chroot_fname(fname)):
                continue
            self.create_fname(fname)

        for fname in self.diverts:
            os.unlink(self.chroot_fname(fname))
            cmd = 'dpkg-divert --remove --rename ' + fname
            self.cmd(cmd)

        if os.path.isfile(self.chroot_fname('/usr/sbin/update-grub')):
            fh = None
            try:
                fh = open(self.chroot_fname('/etc/kernel-img.conf'), 'a')
                print >>fh, 'postinst_hook = /usr/sbin/update-grub'
                print >>fh, 'postrm_hook   = /usr/sbin/update-grub'
            except IOError, e:
                raise FllChrootError('failed to open kernel-img.conf: ' + e)
            finally:
                if fh:
                    fh.close()

    def chroot_fname(self, filename):
        return os.path.join(self.path, filename.lstrip('/'))

    def create_fname(self, filename, mode=0644):
        fh = None
        try:
            fh = open(self.chroot_fname(filename), 'w')

            if filename == '/usr/sbin/policy-rc.d':
                print >>fh, '#!/bin/sh'
                print >>fh, 'echo "$0 denied action: \`$1 $2\'" >&2'
                print >>fh, 'exit 101'

            elif filename == '/etc/fstab':
                print >>fh, '# /etc/fstab: static file system information.'

            elif filename == '/etc/hostname':
                print >>fh, self.hostname

            elif filename == '/etc/hosts':
                print >>fh, '127.0.0.1\tlocalhost'
                print >>fh, '127.0.0.1\t' + self.hostname + '\n'
                print >>fh, '# Below lines are for IPv6 capable hosts'
                print >>fh, '::1     ip6-localhost ip6-loopback'
                print >>fh, 'fe00::0 ip6-localnet'
                print >>fh, 'ff00::0 ip6-mcastprefix'
                print >>fh, 'ff02::1 ip6-allnodes'
                print >>fh, 'ff02::2 ip6-allrouters'
                print >>fh, 'ff02::3 ip6-allhosts'

            elif filename == '/etc/kernel-img.conf':
                print >>fh, 'do_bootloader = No'
                print >>fh, 'warn_initrd   = No'

            elif filename == '/etc/network/interfaces':
                print >>fh, '# /etc/network/interfaces'
                print >>fh, '# Configuration file for ifup(8) and ifdown(8).\n'
                print >>fh, '# The loopback interface'
                print >>fh, 'auto lo'
                print >>fh, 'iface lo inet loopback'

        except IOError:
            raise FllChrootError('failed to write: ' + filename)
        finally:
            if fh:
                fh.close()
                os.chmod(self.chroot_fname(filename), mode)

    def mountvirtfs(self):
        """Mount /sys, /proc, /dev/pts virtual filesystems in the chroot."""
        virtfs = {'devpts': 'dev/pts', 'proc': 'proc', 'sysfs': 'sys'}

        for v in virtfs.items():
            cmd = ['mount', '-t', v[0], 'none', os.path.join(self.path, v[1])]
            retv = subprocess.call(cmd)
            if retv != 0:
                raise FllChrootError('failed to mount virtfs: ' + v[0])

    def umountvirtfs(self):
        """Unmount virtual filesystems that are mounted within the chroot."""
        umount = list()

        try:
            for line in open('/proc/mounts'):
                (dev, mnt, fs, options, d, p) = line.split()
                if mnt.startswith(self.path):
                    umount.append(mnt)
        except IOError:
            raise FllChrootError('failed to open /proc/mounts for reading')

        umount.sort(key=len)
        umount.reverse()

        for mnt in umount:
            retv = subprocess.call(['umount', mnt])
            if retv != 0:
                subprocess.call(['umount', '-l', mnt])
                # Raise an error: even though the lazy umount may have
                # succeeded, something may be wrong.
                raise FllChrootError('failed to umount : ' + mnt)

    def nuke(self):
        """Remove the chroot from filesystem. All mount points in chroot
        will be umounted prior to attempted removal."""
        self.umountvirtfs()

        try:
            shutil.rmtree(self.path)
        except:
            raise FllChrootError('failed to nuke chroot: ' + self.path)

    def cmd(self, cmd):
        """Execute a command in the chroot."""
        if isinstance(cmd, str):
            cmd = cmd.split()

        print ' '.join(cmd)

        pid = os.fork()
        if pid == 0:
            self.mountvirtfs()
            os.chroot(self.path)
            os.chdir('/')
            os.execvpe(cmd[0], cmd, self.env)
        else:
            (id, retv) = os.waitpid(pid, 0)
            self.umountvirtfs()
            if retv != 0:
                raise FllChrootError('chrooted cmd failed: ' + ' '.join(cmd))
