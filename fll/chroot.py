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
    """
    path = None
    env = {'LANGUAGE': 'C', 'LC_ALL': 'C', 'LANG' : 'C', 'HOME': '/root',
           'PATH': '/usr/sbin:/usr/bin:/sbin:/bin', 'SHELL': '/bin/bash',
           'DEBIAN_FRONTEND': 'noninteractive', 'DEBIAN_PRIORITY': 'critical',
           'DEBCONF_NOWARNINGS': 'yes'}

    def __init__(self, path):
        self.path = path

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
