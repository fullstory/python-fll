"""
This is the fll.chroot module, it provides a class for bootstrapping
and executing commands within a chroot.

Authour:   Kel Modderman
Copyright: Copyright (C) 2010 Kel Modderman <kel@otaku42.de>
License:   GPL-2
"""

import fll.misc
import os
import subprocess
import shlex
import shutil
import signal
import sys
import tempfile


class ChrootError(Exception):
    """
    An Error class for use by Chroot.
    """
    pass


class Chroot(object):
    """
    A class which provides the ability to bootstrap and execute commands
    within a chroot.

    Options        Type   Description
    --------------------------------------------------------------------------
    rootdir      - (str)  path to root of chroot
    architecture - (str)  architecture of chroot
    config       - (dict) the 'chroot' section of fll.config.Config object
    """
    diverts = ['/usr/sbin/policy-rc.d', '/sbin/modprobe', '/sbin/insmod',
               '/usr/sbin/update-grub', '/usr/sbin/update-initramfs',
               '/sbin/initctl', '/sbin/start-stop-daemon']

    def __init__(self, rootdir=None, architecture=None, config={}):
        if rootdir is None:
            raise AptLibError('must specify rootdir=')
        if architecture is None:
            raise AptLibError('must specify architecture=')
        if not config:
            raise AptLibError('must specify config=')

        self.rootdir = os.path.realpath(rootdir)
        self.architecture = architecture
        self.config = config

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        if not self.config['preserve']:
            self.nuke()

    def bootstrap(self):
        """Bootstrap a Debian chroot. By default it will bootstrap a minimal
        sid chroot with cdebootstrap."""
        utility = self.config['bootstrap']['utility']
        uri = self.config['bootstrap']['uri']
        suite = self.config['bootstrap']['suite']
        flavour = self.config['bootstrap']['flavour']
        quiet = self.config['bootstrap']['quiet']
        if not quiet:
            quiet = self.config['quiet']
        verbose = self.config['bootstrap']['verbose']
        # default verbosity level is noisy enough imo
        #if not verbose:
        #    verbose = self.config['verbose']
        debug = self.config['bootstrap']['debug']
        if not debug:
            debug = self.config['debug']
        include = self.config['bootstrap']['include']
        exclude = self.config['bootstrap']['exclude']

        cmd = [utility]

        if utility == 'cdebootstrap':
            cmd.append('--flavour=' + flavour)
        elif utility == 'debootstrap':
            if flavour == 'minimal':
                flavour = 'minbase'
            elif flavour == 'build':
                flavour = 'buildd'
            cmd.append('--variant=' + flavour)
        else:
            raise ChrootError('unknown utility: ' + utility)

        cmd.append('--arch=' + self.architecture)

        if include:
            cmd.append('--include=' + include)
        if exclude:
            cmd.append('--exclude=' + exclude)
        if verbose:
            cmd.append('--verbose')        
        if debug and utility == 'cdebootstrap':
            cmd.append('--debug')
        if quiet and utility == 'cdebootstrap':
            cmd.append('--quiet')
        
        cmd.append(suite)
        cmd.append(self.rootdir)
        cmd.append(uri)

        try:
            fll.misc.cmd(cmd)
        except OSError:
            raise ChrootError('bootstrap command failed: %s' % ' '.join(cmd))

        # Some flavours use cdebootstrap-helper-rc.d, some don't. We'll
        # impliment our our own policy-rc.d for consistency.
        if utility == 'cdebootstrap':
            self.cmd('dpkg --purge cdebootstrap-helper-rc.d'.split(),
                     silent=self.config['quiet'])

    def debconf_set_selections(self, selections):
        dss = '/usr/bin/debconf-set-selections'

        if not os.path.exists(self.chroot_path(dss)):
            return

        cmd = [dss]
        if self.config['quiet'] is False:
            cmd.append('--verbose')

        with tempfile.NamedTemporaryFile(dir=self.rootdir, prefix='debconf_') \
             as fh:
            for line in selections:
                print >>fh, line
            fh.flush()
            cmd.append(self.chroot_path_rel(fh.name))
            self.cmd(cmd)

    def init(self):
        """Configure the basics to get a functioning chroot."""
        for fname in ('/etc/hosts', '/etc/resolv.conf'):
            if os.path.isfile(self.chroot_path(fname)):
                os.unlink(self.chroot_path(fname))
            shutil.copy(fname, self.chroot_path(fname))

        for fname in ('/etc/fstab', '/etc/hostname',
                      '/etc/network/interfaces'):
            self.create_file(fname)

        for fname in self.diverts:
            cmd = 'dpkg-divert --add --local --divert ' + fname + '.REAL'
            cmd += ' --rename ' + fname
            self.cmd(cmd, silent=self.config['quiet'])
            self.create_file(fname, mode=0755)

        debconf = ['man-db man-db/auto-update boolean false']
        self.debconf_set_selections(debconf)

    def deinit(self):
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
            self.cmd(cmd, silent=self.config['quiet'])

        debconf = ['man-db man-db/auto-update boolean true']
        self.debconf_set_selections(debconf)
        if os.path.exists(self.chroot_path('/usr/bin/mandb')):
            cmd = ['/usr/bin/mandb', '--create']
            if self.config['quiet']:
                cmd.append('--quiet')
            self.cmd(cmd)

    def chroot_path(self, path):
        return os.path.join(self.rootdir, path.lstrip('/'))

    def chroot_path_rel(self, path):
        return path.replace(self.rootdir, '')

    def create_file(self, filename, mode=0644):
        fh = None
        try:
            fh = open(self.chroot_path(filename), 'w')

            if filename in self.diverts:
                if filename.endswith('policy-rc.d'):
                    retv = 101
                else:
                    retv = 0

                print >>fh, """\
#!/bin/sh
echo 1>&2
echo "Command denied: $0 $@" 1>&2
echo 1>&2
exit %d""" % retv

            elif filename == '/etc/fstab':
                print >>fh, """\
# /etc/fstab: static file system information."""

            elif filename == '/etc/hostname':
                print >>fh, 'chroot'

            elif filename == '/etc/hosts':
                print >>fh, """\
127.0.0.1\tlocalhost
127.0.0.1\tchroot

# Below lines are for IPv6 capable hosts
::1     ip6-localhost ip6-loopback
fe00::0 ip6-localnet
ff00::0 ip6-mcastprefix
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
ff02::3 ip6-allhosts"""

            elif filename == '/etc/network/interfaces':
                print >>fh, """\
auto lo
iface lo inet loopback"""

        except IOError:
            raise ChrootError('failed to write: ' + filename)
        finally:
            if fh:
                fh.close()
                os.chmod(self.chroot_path(filename), mode)

    def mountvirtfs(self):
        """Mount /sys, /proc, /dev/pts virtual filesystems in the chroot."""
        virtfs = {'devpts': '/dev/pts', 'proc': '/proc', 'sysfs': '/sys'}

        for vfstype, mnt in virtfs.items():
            cmd = ['mount', '-t', vfstype, 'none', self.chroot_path(mnt)]
            try:
                subprocess.check_call(cmd, preexec_fn=fll.misc.restore_sigpipe)
            except (subprocess.CalledProcessError, OSError):
                raise ChrootError('failed to mount virtfs: ' + mnt)

    def umountvirtfs(self):
        """Unmount virtual filesystems that are mounted within the chroot."""
        umount = list()

        with open('/proc/mounts') as mounts:
            for line in mounts:
                name, mnt, vfstype, opts, freqno, passno = line.split()
                if mnt.startswith(self.rootdir):
                    umount.append(mnt)

        umount.sort(key=len)
        umount.reverse()

        for mnt in umount:
            try:
                subprocess.check_call(['umount', mnt],
                                      preexec_fn=fll.misc.restore_sigpipe)
            except (subprocess.CalledProcessError, OSError):
                raise ChrootError('failed to umount virtfs: ' + mnt)

    def nuke(self):
        """Remove the chroot from filesystem. All mount points in chroot
        will be umounted prior to attempted removal."""
        self.umountvirtfs()

        try:
            if os.path.isdir(self.rootdir):
                print 'HOST nuke(%s)' % self.rootdir
                shutil.rmtree(self.rootdir)
        except IOError:
            raise ChrootError('failed to nuke chroot: ' + self.rootdir)

    def _chroot(self):
        """Convenience function so that subprocess may be executed in chroot
        via preexec_fn. Restore SIGPIPE."""
        fll.misc.restore_sigpipe()
        os.chroot(self.rootdir)
        os.chdir('/')

    def cmd(self, cmd, pipe=False, quiet=False, silent=False):
        """Execute a command in the chroot."""
        if isinstance(cmd, str):
            cmd = shlex.split(cmd)

        if silent is False:
            print 'CHROOT %s %s' % (self.rootdir, ' '.join(cmd))

        devnull = output = None

        if quiet is False:
            quiet = self.config['quiet']

        self.mountvirtfs()
        try:
            if pipe:
                proc = subprocess.Popen(cmd, preexec_fn=self._chroot, cwd='/',
                                        stdout=subprocess.PIPE)
                output = proc.communicate()[0]
            elif quiet or silent:
                devnull = os.open(os.devnull, os.O_RDWR)
                proc = subprocess.Popen(cmd, preexec_fn=self._chroot, cwd='/',
                                        stdout=devnull)
                proc.wait()
            else:
                proc = subprocess.Popen(cmd, preexec_fn=self._chroot, cwd='/')
                proc.wait()
        except OSError, e:
            raise ChrootError('chrooted command failed: %s' % e)
        finally:
            self.umountvirtfs()
            if devnull:
                os.close(devnull)

        if proc.returncode != 0:
            raise ChrootError('chrooted command returncode=%d: %s' %
                              (proc.returncode, ' '.join(cmd)))

        if pipe:
            return output
