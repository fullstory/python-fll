"""
This is the fll.locales module, it provides a class for detecting
locale support packages given a list/dict of packages, apt_pkg cache
object and a dict of package -> locale package name prefix strings.

Author:    Kel Modderman
Copyright: Copyright (C) 2008 Kel Modderman <kel@otaku42.de>
License:   GPL-2
"""


"""
This dict contains fallback strings for specific locales. It is used
by the very private method, __compute_locale_loc_suf_list, of the
FllLocales class.
"""
FLL_LOCALE_DEFAULTS = {
    'be': 'be_BY',
    'cs': 'cs_CZ',
    'da': 'da_DK',
    'en': 'en_US',
    'el': 'el_GR',
    'ga': 'ga_IE',
    'he': 'he_IL',
    'ja': 'ja_JP',
    'ko': 'ko_KR',
    'nb': 'nb_NO',
    'nn': 'nn_NO',
    'pt': 'pt_BR',
    'sl': 'sl_SI',
    'zh': 'zh_CN'
}


class FllLocalesError(Exception):
    """
    An Error class for use by FllLocales.
    """
    pass


class FllLocales(object):
    """
    A class which provides the ability to determine lists of locale specific
    Debian packages using it's detect_locale_packages method.

    Arguments:
    cache    - an apt_pkg cache object
    packages - a list or dict of package names which are installed, or are
               going to be installed. Locale specific packages are selected
               for packages in this data structure.
    map      - a dict which maps package names with a list of package prefixes
               from which the locale string pattern matching can be used
               to match locale support packages. The prefered input for map is:
               ConfigObj('data/fll-locales-pkg-map').
    """
    def __init__(self, cache, packages, map):
        self.loc_pkgs_set = set()
        for pkg in cache.packages:
            if not pkg.version_list:
                continue
            if pkg.name not in packages:
                continue
            for loc_pkg in map.keys():
                if pkg.name == loc_pkg:
                    loc_pkg_prefix_list = map.get(loc_pkg)
                    for loc_pkg_prefix in loc_pkg_prefix_list:
                        self.loc_pkgs_set.add(loc_pkg_prefix)
                    break

        self.loc_pkgs_list_dict = dict()
        for loc_pkg in self.loc_pkgs_set:
            self.loc_pkgs_list_dict[loc_pkg] = list()
        for pkg in cache.packages:
            if not pkg.version_list:
                continue
            for loc_pkg in self.loc_pkgs_set:
                if pkg.name.startswith(loc_pkg + '-'):
                    self.loc_pkgs_list_dict[loc_pkg].append(pkg.name)

    def __compute_locale_loc_suf_list(self, locale):
        """
        Compute a list of locale package name suffixes. The sequence of
        suffixes are in preferential order, the lowest index being most
        preferential.

        This is a very private method, used by detect_locale_packages.

        Arguments:
        locale - a locale string (eg. en_AU, pt_PT etc.)
        """
        loc_suf_list = list()
        try:
            ll, cc = locale.lower().split('_')
        except ValueError, e:
            raise FllLocalesError(e)
        loc_suf_list.append(ll + '-' + cc)
        loc_suf_list.append(ll + cc)
        loc_suf_list.append(ll)

        default = FLL_LOCALE_DEFAULTS.get(ll)
        if default and default != locale:
            try:
                ll, cc = default.lower().split('_')
            except ValueError, e:
                raise FllLocalesError(e)
            loc_suf_list.append(ll + '-' + cc)
            loc_suf_list.append(ll + cc)
        else:
            loc_suf_list.append(ll + '-' + ll)
            loc_suf_list.append(ll + ll)

        if ll != 'en':
            loc_suf_list.append('i18n')

        return loc_suf_list

    def detect_locale_packages(self, locale):
        """
        Process the data structures created at FllLocales instantiation and
        return a list of package names which are the likely best candidates
        for the locale string given as argument.

        Arguments:
        locale - a locale string (eg. en_AU, pt_PT etc.)
        """
        suffixes = self.__compute_locale_loc_suf_list(locale)

        loc_pkg_dict = dict()
        for pkg in self.loc_pkgs_set:
            loc_pkgs_list = self.loc_pkgs_list_dict.get(pkg)
            if not loc_pkgs_list:
                continue
            if pkg not in loc_pkg_dict:
                loc_pkg_dict[pkg] = dict()
            for loc_pkg in loc_pkgs_list:
                for idx, suf in enumerate(suffixes):
                    if loc_pkg == '-'.join([pkg, suf]):
                       loc_pkg_dict[pkg][idx] = loc_pkg

        packages = list()
        for pkg in self.loc_pkgs_set:
            pkg_candidates = loc_pkg_dict.get(pkg)
            if not pkg_candidates:
                continue
            best = min(pkg_candidates)
            packages.append(pkg_candidates[best])

        return packages
