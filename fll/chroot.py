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


class ChrootError(Exception):
    """
    An Error class for use by Chroot.
    """
    pass


class Chroot(object):
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

    def __del__(self):
        self.nuke()

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
            raise ChrootError('unknown bootstrapper: ' + bootstrapper)

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
            raise ChrootError('bootstrap() requires a mirror')

        print ' '.join(cmd)

        try:
            subprocess.check_call(cmd)
        except:
            raise ChrootError('bootstrap commmand failed: ' + ' '.join(cmd))

        # Some flavours use cdebootstrap-helper-rc.d, some don't. We'll
        # impliment our our own policy-rc.d for consistency.
        if bootstrapper == 'cdebootstrap':
            self.cmd('dpkg --purge cdebootstrap-helper-rc.d'.split())

    def prep_chroot(self):
        """Configure the basics to get a functioning chroot."""
        for fname in ('/etc/hosts', '/etc/resolv.conf'):
            os.unlink(self.chroot_path(fname))
            shutil.copy(fname, self.chroot_path(fname))

        for fname in ('/etc/fstab', '/etc/hostname'):
            self.create_file(fname)

        for fname in self.diverts:
            cmd = 'dpkg-divert --add --local --divert ' + fname + '.REAL'
            cmd += ' --rename ' + fname
            self.cmd(cmd)

            if fname == '/usr/sbin/policy-rc.d':
                self.create_file(fname, mode=0755)
            else:
                os.symlink('/bin/true', self.chroot_path(fname))

    def post_chroot(self):
        """Undo any changes in the chroot which should be undone. Make any
        final configurations."""
        for fname in ('/etc/hosts', '/etc/resolv.conf'):
            # /etc/resolv.conf (and possibly others) may be a symlink to an 
            # absolute path - so do not clobber the host's configuration.
            if os.path.islink(self.chroot_path(fname)):
                continue
            self.create_file(fname)

        for fname in self.diverts:
            os.unlink(self.chroot_path(fname))
            cmd = 'dpkg-divert --remove --rename ' + fname
            self.cmd(cmd)

    def chroot_path(self, path):
        return os.path.join(self.path, path.lstrip('/'))

    def create_file(self, filename, mode=0644):
        fh = None
        try:
            fh = open(self.chroot_path(filename), 'w')

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

        except IOError:
            raise ChrootError('failed to write: ' + filename)
        finally:
            if fh:
                fh.close()
                os.chmod(self.chroot_path(filename), mode)

    def mountvirtfs(self):
        """Mount /sys, /proc, /dev/pts virtual filesystems in the chroot."""
        virtfs = {'devpts': '/dev/pts', 'proc': '/proc', 'sysfs': '/sys'}

        for type, dir in virtfs.items():
            cmd = ['mount', '-t', type, 'none', self.chroot_path(dir)]
            try:
                subprocess.check_call(cmd)
            except:
                raise ChrootError('failed to mount virtfs: ' + dir)

    def umountvirtfs(self):
        """Unmount virtual filesystems that are mounted within the chroot."""
        umount = list()

        try:
            for line in open('/proc/mounts'):
                (dev, mnt, fs, options, d, p) = line.split()
                if mnt.startswith(self.path):
                    umount.append(mnt)
        except IOError:
            raise ChrootError('failed to open /proc/mounts for reading')

        umount.sort(key=len)
        umount.reverse()

        for mnt in umount:
            try:
                subprocess.check_call(['umount', mnt])
            except:
                raise ChrootError('failed to umount virtfs: ' + mnt)

    def nuke(self):
        """Remove the chroot from filesystem. All mount points in chroot
        will be umounted prior to attempted removal."""
        self.umountvirtfs()

        try:
            if os.path.isdir(self.path):
                shutil.rmtree(self.path)
        except:
            raise ChrootError('failed to nuke chroot: ' + self.path)

    def __chroot(self):
        """Convenience function so that subprocess may be executed in chroot
        via preexec_fn."""
        os.chroot(self.path)

    def cmd(self, cmd):
        """Execute a command in the chroot."""
        if isinstance(cmd, str):
            cmd = cmd.split()

        print ' '.join(cmd)

        self.mountvirtfs()

        try:
            proc = subprocess.Popen(cmd, preexec_fn=self.__chroot,
                                    env=self.env, cwd='/')
            proc.wait()
            assert(proc.returncode == 0)
        except:
            raise ChrootError('chrooted command failed: ' + ' '.join(cmd))
        finally:
            self.umountvirtfs()

    def cmd_stdout(self, cmd):
        """Execute a command in the chroot. Return stdout."""
        if isinstance(cmd, str):
            cmd = cmd.split()

        print ' '.join(cmd)

        self.mountvirtfs()

        try:
            proc = subprocess.Popen(cmd, preexec_fn=self.__chroot,
                                    env=self.env, cwd='/',
                                    stdout=subprocess.PIPE)
            stdout = proc.communicate()[0]
            assert(proc.returncode == 0)
        except:
            raise ChrootError('chrooted command failed: ' + ' '.join(cmd))
        finally:
            self.umountvirtfs()

        return stdout
