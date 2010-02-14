import os

from configobj import ConfigObj
from validate import Validator

class TestConfig(object):
    def setUp(self):
        pass

    def test1_config_validate(self):
        conffile = 'conf/fll.conf'
        specfile = 'conf/fll.conf.spec'

        conf = ConfigObj(conffile, configspec=specfile)
        validator = Validator()
        results = conf.validate(validator)
        assert results == True

    def test2_config_invalid(self):
        conffile = 'tests/test1_config_validate.test2.conf'
        specfile = 'conf/fll.conf.spec'

        conf = ConfigObj(conffile, configspec=specfile)
        validator = Validator()
        results = conf.validate(validator)
        assert results['apt']['sources']['distro']['suite'] == False
        assert results['apt']['sources']['distro']['components'] == False

    def tearDown(self):
        pass
