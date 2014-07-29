"""
This is the fll.distro module, it abstracts the 'distro' section of an
fll.config.Config object. It provides methods for writing the
/etc/distro-release and /etc/default/distro files.

Author:    Kel Modderman
Copyright: Copyright (C) 2010 Kel Modderman <kel@otaku42.de>
Copyright: Copyright (C) 2014 Niall Walsh <niallwalsh@celtux.org>
License:   GPL-2
"""

import os

class DistroError(Exception):
    pass


class Distro(object):
    """
    A class which provides specific setup on top of the chroot
    
    Options        Type   Description
    --------------------------------------------------------------------------
    chroot       - (Chroot)  Chroot object
    config       - (dict) the 'distro' section of fll.config.Config object
    """

    def __init__(self, chroot=None, config={}):
        if chroot is None:
            raise DistroError('must specify chroot=')

        self.chroot = chroot
        self.config = config

    def init(self):
        self.password()

    def password(self):
        """Setup password(s) in the chroot or passwordless access"""
        pwset = 0
        for user in [ u[13:]
          for u in self.config if u[:13]=='FLL_PASSWORD_' and len(u)>13 ]:
            if not user == 'root':
                self.chroot.cmd([ 'adduser' , '--disabled-password',
                        '--gecos', 'Auto User,,,', user ])
            self.chroot.cmd([ 'usermod', '-p', 
                    self.config[ 'FLL_PASSWORD_%s' % user ], user ])
            pwset = pwset + 1
        if pwset == 0 and os.path.exists(self.chroot.chroot_path('/lib/systemd/system/getty@.service')):
            """if no passwords given, set autologin as root"""
            with open(self.chroot.chroot_path('/lib/systemd/system/getty@.service')) as lines:
                with open(self.chroot.chroot_path('/etc/systemd/system/getty@.service'),'w') as outfile:
                    print "setting autologin as root"
                    for line in lines:
                        if line.startswith('ExecStart='):
                            outfile.write(line.replace('getty','getty -a root'))
                        else:
                            outfile.write(line)
            self.chroot.cmd('ln -fs /etc/systemd/system/getty@.service /etc/systemd/system/getty.target.wants/getty@tty1.service'.split())
            self.chroot.cmd('ln -fs getty@.service /etc/systemd/system/autovt@.service'.split())
