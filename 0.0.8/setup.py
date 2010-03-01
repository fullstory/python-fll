#!/usr/bin/python

from distutils.core import setup

fll_data_files = [('/usr/share/fll/data', ['data/locales-pkg-map'])]
fll_scripts = ['fll_detect_loc_pkgs']

setup(
    name = 'python-fll',
    author = 'Kel Modderman',
    author_email = 'kel@otaku42.de',
    license = 'GPL-2',
    description = 'FULLSTORY',
    packages = ['fll'],
    data_files = fll_data_files,
    scripts = fll_scripts,
)
