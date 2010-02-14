import glob
import os
import sys

from configobj import ConfigObj
from fll.apt import Apt, AptError
from fll.chroot import Chroot, ChrootError

class TestAptSources(object):
    def setUp(self):
        os.makedirs('tests/root/etc/apt/sources.list.d/')
        self.chroot = Chroot('tests/root')
        self.apt = Apt(self.chroot)

    def test1_create_lists(self):
        sources = ConfigObj("tests/test_apt_sources.test1.conf")
        self.apt.prep_apt_sources(sources)
        
        path = self.chroot.chroot_path('/etc/apt/sources.list.d/*.list')
        lists = glob.glob(path)
        print lists
        #raw_input('Check tests/root/etc/apt/, press return key.')
        assert len(lists) == 4

    def tearDown(self):
        self.chroot.nuke()
