import glob
import os
import sys

from configobj import ConfigObj
from fll.aptlib import AptLib, AptLibError
from fll.chroot import Chroot, ChrootError

class TestAptSources(object):
    def setUp(self):
        os.makedirs('tests/root/etc/apt/sources.list.d/')
        self.chroot = Chroot('tests/root')
        sources = ConfigObj("tests/test2_apt_sources.conf")
        self.apt = AptLib(self.chroot, sources)

    def test1_create_lists(self):
        self.apt.prep_apt_sources()
        path = self.chroot.chroot_path('/etc/apt/sources.list.d/*.list')
        lists = glob.glob(path)
        assert len(lists) == 4

    def tearDown(self):
        self.chroot.nuke()
