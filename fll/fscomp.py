"""
This is the fll.fsimage module which contains a class responsible for
helping create a filesystem image of a chroot.

Author:    Kel Modderman
Copyright: Copyright (C) 2010 Kel Modderman <kel@otaku42.de>
Copyright: Copyright (C) 2013-2014 Niall Walsh <niallwalsh@celtux.org>
License:   GPL-2
"""

import fll.misc
import os
import shutil
import time

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
        self.output=list()
        self.depends=[]
        self.ts=''
        if (self.config['compression'] == 'squashfs'):
            self.depends.append('squashfs-tools')
        elif (self.config['compression'] == 'mkfs'):
            self.depends.append('rsync')
        if (('wrap' in self.config) and ('iso' in self.config['wrap'])):
            # ,'grub-efi-amd64-bin','grub-efi-ia32-bin'
            self.depends.extend(['grub-pc','xorriso'])

    def compress(self):
        """create whatever is set for compression and wrap it"""
        # create the stamp file to identify the fs
        self.stamp()
        if (self.config['compression'] == 'squashfs'):
            self.squash()
        elif (self.config['compression'] == 'tar'):
            self.tar()
        elif (self.config['compression'] == 'mkfs'):
            self.mkfs()
        self.wrap()

    def squash(self):
        """create a squashfs file of the chroot"""
        config = self.config['squashfs']
        output = None
        if (len(config['file']) > 0):
            filename = config['file']
            output = filename
        else:
            filename = 'tmp/squash'
        cmd = [ 'mksquashfs', '.', filename, '-comp', config['compressor'] ]
        if (config['compressor'] == 'xz'):
            cmd.extend('-Xbcj', 'x86')
        cmd.extend(['-wildcards', '-ef', self.excludesfile(config,filename)])
        self.chroot.cmd(cmd)
        if (output != None):
            shutil.move(self.chroot.chroot_path(filename),output)
            self.output.append(output)
        else:
            self.output.append(filename)

    def tar(self):
        """create a tar of the chroot"""
        config = self.config['tar']
        output = None
        if (len(config['file']) > 0):
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
        if (output != None):
            shutil.move(self.chroot.chroot_path(filename),output)
            self.output.append(output)
        else:
            self.output.append(filename)

    def mkfs(self):
        """create a filesystem image of the chroot"""
        config = self.config['mkfs']
        output = None
        if (len(config['file']) > 0):
            filename = config['file']
            output = filename
        else:
            filename = 'tmp/rootfs'
        self.chroot.cmd([ 'dd', 'if=/dev/zero',
                          'of=%s' % filename,
                          'bs=1',
                          'count=1', 'seek=%i' % (config['size']*2**20) ])
        self.chroot.cmd([ 'mkfs', '-t', config['type'], filename ])
        if (not os.path.exists('/dev/loop0')):
            fll.misc.cmd(['insmod', 'loop'])
        fll.misc.cmd(['mount', self.chroot.chroot_path(filename),
                                self.chroot.chroot_path('/mnt') ])
        self.chroot.cmd(['rsync', '-a', 
                         '--exclude-from=%s' % self.excludesfile(config,filename),
                         '/', '/mnt/' ])
        fll.misc.cmd(['umount', self.chroot.chroot_path('/mnt') ])
        size = self.chroot.cmd(['du', '-m', filename ],
                                pipe=True).split()[0]
        # factor is %, size is mb, round up round number of M
        resize = "%iM" % (1+int(config['factor']*int(size)/100))
        if ( not (os.path.exists(self.chroot.chroot_path('/etc/mtab')))):
            os.symlink('/proc/mounts',self.chroot.chroot_path('/etc/mtab'))
        self.chroot.cmd([ 'resize2fs', filename, resize ])
        self.chroot.cmd([ 'truncate', '-s', resize, filename ])
        if output != None:
            shutil.move(self.chroot.chroot_path(filename),output)
            self.output.append(output)
        else:
            self.output.append(filename)

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

    def wrap(self):
        """run the list in wrap"""
        if ( (self.config['wrap'][0] == 'none' ) or
             (len(self.output) == 0) ):
            return()
        for wrapper in self.config['wrap']:
            if wrapper == 'iso':
                config = self.config['iso']
                input = self.output[ len(self.output)-1 ]
                output = None
                if (len(config['file']) > 0):
                    filename = config['file']
                    output = filename
                else:
                    filename = '%s.iso' % input
                os.mkdir(self.chroot.chroot_path('/tmp/iso'))
                #self.chroot.cmd(['cp', '-a', '/boot', '/tmp/iso/'])
                self.stage('/tmp/iso')
                cmd = [ 'grub-mkrescue', '-o', filename, '/tmp/iso', '--',
                        '--append_partition', '2', '0x83', input ]
            self.chroot.cmd(cmd)
        if output != None:
            shutil.move(self.chroot.chroot_path(filename),output)
            self.output.append(output)
        else:
            self.output.append(filename)

    def stage(self,path):
        """put required files needed in path"""
        chroot = self.chroot
        if ( not os.path.exists( chroot.chroot_path( path ) ) ):
            return()
        chpath = chroot.chroot_path('/tmp/iso')
        bpath = os.path.join(chpath, 'boot')
        gpath = os.path.join(bpath, 'grub')
        os.mkdir(bpath)
        os.mkdir(gpath)
        ks = list()
        for v in chroot.detectLinuxVersions():
            for t in [ 'x', 'z']:
                kernel = chroot.chroot_path('boot/vmlinu%s-%s' % (t,v))
                if (os.path.exists(kernel)):
                    shutil.copy(kernel,bpath)
                    ks.append([kernel[kernel.rfind('/'):]])
            initrd = os.path.join(chroot.chroot_path('boot/initrd.img-' + v))
            if (os.path.isfile(initrd)):
                shutil.copy(initrd,bpath)
                ks[len(ks)-1].append(initrd[initrd.rfind('/'):])
        if (len(ks)==0):
            return
        gcfg = open(os.path.join(gpath,'grub.cfg'),'w')
        gcfg.write('insmod search\n')
        gcfg.write('search --no-floppy --file --set dev %s\n' % self.ts)
        gcfg.write('probe -s uuid -u $dev\n')
        for k in ks:
            gcfg.write('menuentry "%s" {\n' % k[0][k[0].find('-'):])
            gcfg.write('  linux /boot/%s root=UUID=$uuid ro quiet systemd.show_status=1\n' % k[0])
            if (len(k)>1):
                gcfg.write('  initrd /boot/%s\n' % k[1])
            gcfg.write('}\n')
        gcfg.close()

    def stamp(self):
        """"""
        ts = list()
        for t in time.gmtime():
            ts.append('%i' % t)
        stamp = '/boot/'+'-'.join(ts)
        open(self.chroot.chroot_path(stamp),'w').close()
        self.ts = stamp
