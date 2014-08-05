"""
This is the fll.fsimage module which contains a class responsible for
helping create a filesystem image of a chroot.

Author:    Kel Modderman
Copyright: Copyright (C) 2010 Kel Modderman <kel@otaku42.de>
Copyright: Copyright (C) 2013-2014 Niall Walsh <niallwalsh@celtux.org>
License:   GPL-2
"""

import fll.misc
import shutil

class FsCompError(Exception):
    pass


class FsComp(object):
    taropt = dict( gz='-z', bz='-j', xz='-J', pz='-Ipixz' )
    excludes = [ 'etc/.*lock', 'etc/*-', 'etc/adjtime', 'etc/apt/*~',
                 'etc/blkid.tab', 'etc/console-setup/*.gz', 'etc/localtime',
                 'etc/lvm/archive', 'etc/lvm/backup', 'etc/lvm/cache',
                 'etc/timezone', 'etc/ssh/ssh_host_*key*',
                 'etc/udev/rules.d/70-persistent-*.rules', 'etc/X11/xorg.conf',
                 'lib/init/rw/*', 'media/*', 'media/.*', 'mnt/*', 'proc/*',
                 'root/*', 'root/.*', 'run/*', 'sys/*', 'tmp/*', 'tmp/.*',
                 'usr/bin/qemu-*-static', 'var/cache/apt/*.bin',
                 'var/cache/apt-show-versions/*', 'var/cache/debconf/*-old',
                 'var/lib/alsa/asound.state', 'var/lib/apt/extended_states',
                 'var/lib/apt/lists/*_dists_*', 'var/lib/dbus/machine-id',
                 'var/lib/dpkg/*-old', 'var/run/*' ]
    def __init__(self, chroot=None,config={}):
        self.chroot=chroot
        self.config=config
        self.depends=[]
        if (self.config['compression'] == 'squashfs'):
            self.depends.append('squashfs-tools')

    def compress(self):
        """create whatever is set for compression"""
        if (self.config['compression'] == 'squashfs'):
            self.squash()
        elif (self.config['compression'] == 'tar'):
            self.tar()
        else:
            return

    def squash(self):
        """create a squashfs file of the chroot"""
        config = self.config['squashfs']
        output = '%s.squash' % self.chroot.rootdir
        if ('file' in config):
            filename = config['file']
            output = filename
        else:
            filename = 'tmp/squash'
            filename = '%s.%s' % (filename, config['compressor'])
            output = '%s.%s' % (output, config['compressor'])
        cmd = [ 'mksquashfs', '.', filename, '-comp', config['compressor'] ]
        if (config['compressor'] == 'xz'):
            cmd.extend('-Xbcj', 'x86')
        cmd.extend(['-wildcards', '-ef', self.excludesfile(config,filename)])
        self.chroot.cmd(cmd)
        shutil.move(self.chroot.chroot_path(filename),output)

    def tar(self):
        """create a tar of the chroot"""
        config = self.config['tar']
        output = '%s.tar' % self.chroot.rootdir
        if ('file' in config):
            filename = config['file']
            output = filename
        else:
            filename = 'tmp/rootfs.tar'
            if ('compressor' in config):
                filename = '%s.%s' % (filename, config['compressor'])
                output = '%s.%s' % (output, config['compressor'])
        self.chroot.cmd([ 'tar',
                          '-c', "%s" % self.taropt[config['compressor']],
                          '-f', filename,
                          '-X', self.excludesfile(config,filename), '.' ])
        shutil.move(self.chroot.chroot_path(filename),output)

    def excludesfile(self,config,filename):
        """only the most specific excludes are used
        type config, class config, class data in that order """
        excludes=self.excludes
        if 'exclude' in config:
            excludes = config['exclude']
        elif 'exclude' in self.config:
            excludes = self.config['exclude']
        excludes.append(filename)
        xfile='tmp/excludes'
        fh = open(self.chroot.chroot_path(xfile), 'w')
        print >>fh, "\n".join(excludes) + "\n"
        fh.close()
        return(xfile)

