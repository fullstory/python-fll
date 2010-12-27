#!/usr/bin/python

from distutils.command.build import build
from distutils.command.clean import clean
from distutils.core import setup, Command
from distutils.errors import DistutilsOptionError
import datetime
import optparse
import os


class clean_with_subcommands(clean):
    def run(self):
        for cmd_name in self.get_sub_commands():
            self.run_command(cmd_name)
        clean.run(self)

class clean_manpage(Command):
    description = 'Remove manual pages from setup().'
    user_options = [
        ('manpage=', None, 'manpage file'),
    ]

    def initialize_options(self):
        self.manpage = None

    def finalize_options(self):
        if self.manpage is None:
            raise DistutilsOptionError('\'manpage\' option is required')

    def run(self):
        if os.path.isfile(self.manpage):
            os.unlink(self.manpage)

class build_manpage(Command):
    description = 'Generate manual pages from setup().'
    user_options = [
        ('output=', None, 'output file'),
        ('module=', None, 'module name'),
        ('function=', None, 'optparse function name'),
        ('files=', None, 'list of related files'),
        ('also=', None, 'list of related manpages'),
    ]

    def initialize_options(self):
        self.output = None
        self.module = None
        self.function = None
        self.parser = None
        self.files = None
        self.also = None

    def finalize_options(self):
        if self.output is None:
            raise DistutilsOptionError('\'output\' option is required')
        if self.module is None:
            raise DistutilsOptionError('\'module\' option is required')
        if self.function is None:
            raise DistutilsOptionError('\'function\' option is required')

        mod = __import__(self.module, fromlist=self.module.split('.'))
        self.parser = getattr(mod, self.function)()
        self.parser.formatter = ManPageFormatter()
        self.parser.formatter.set_parser(self.parser)

    def run(self):
        def markup(txt):
            return txt.replace('-', '\\-')

        author = self.distribution.get_author()
        email = self.distribution.get_author_email()
        homepage = self.distribution.get_url()
        today = datetime.date.today().strftime('%Y-%m-%d')

        fh = open(self.output, 'w')

        app = self.parser.get_prog_name()
        section = self.output.split('.')[-1]
        fh.write(markup('.TH %s %s %s\n' % (app, section, today)))

        desc = self.parser.get_description().splitlines()[0].rstrip('.')
        fh.write('.SH NAME\n')
        fh.write(markup('%s - %s\n' % (app, desc)))

        long_desc = self.parser.get_description().splitlines()[2:]
        fh.write('.SH DESCRIPTION\n')
        fh.writelines(['%s\n' % line for line in long_desc])

        usage = self.parser.get_usage()
        usage = usage.replace('%s ' % app, '')
        fh.write('.SH SYNOPSIS\n')
        fh.write('.B %s\n' % markup(app))
        fh.write(usage)

        options = self.parser.format_option_help()
        fh.write('.SH OPTIONS\n')
        fh.write(options)

        if self.files:
            fh.write('.SH FILES\n')
            for f in sorted(self.files.split()):
                fh.write('.IP \\(bu\n%s\n' % markup(f))

        if self.also:
            fh.write('.SH SEE ALSO\n')
            for m in sorted(self.also.split()):
                fh.write('.IP \\(bu\n%s\n' % markup(m))

        if homepage and homepage != 'UNKNOWN':
            fh.write('.SH HOMEPAGE\n')
            fh.write('The latest info about \\fB%s\\fR is at\n' % markup(app))
            fh.write('.UR %s\n.UE\n' % markup(homepage))

        if author and author != 'UNKNOWN':
            fh.write('.SH AUTHORS\n')
            fh.write('%s\n' % markup(author))

            if email and email != 'UNKNOWN':
                fh.write('.UR %s\n.UE\n' % markup(email))

            fh.write('.SH COPYRIGHT\n')
            fh.write('Copyright \(co %s %s.\n' %
                     (today.split('-')[0], markup(author)))

        fh.close()


class ManPageFormatter(optparse.HelpFormatter):
    def __init__(self, indent_increment=2, max_help_position=24, width=None,
                 short_first=1):
        optparse.HelpFormatter.__init__(self, indent_increment,
                                        max_help_position, width, short_first)

    def _markup(self, txt):
        return txt.replace('-', '\\-')

    def format_usage(self, usage):
        usage = '.BI %s\n' % usage
        usage = usage.replace('=', '= ')
        usage = usage.replace('[', '\n[\\fI')
        usage = usage.replace(']', '\\fR]')
        return self._markup(usage)

    def format_description(self, description):
        result = []
        for line in description.splitlines():
            line = line.strip()
            if len(line) == 0:
                line = '.PP'
            if line.startswith('* '):
                line = line.replace('* ', '.IP \\(bu\n')
            result.append('%s\n' % line)
        return self._markup(''.join(result))

    def format_heading(self, heading):
        if self.level == 0:
            return ''
        return '.TP\n%s\n' % self._markup(heading.upper())

    def format_option(self, option):
        result = []
        opt_str = self._markup(self.option_strings[option])
        if opt_str.find(',') >= 0:
            opt_s, opt_l = opt_str.split(',')
            if opt_l.find('=') >= 0:
                opt_l = opt_l.replace('=', '= ')
                result.append('.TP\n.BI %s "\\fR,\\fB" " " %s\n' %
                              (opt_s, opt_l))
            else:
                result.append('.TP\n.BI %s "" \\fR,\\fB " " %s\n' %
                              (opt_s, opt_l))
        else:
            result.append('.TP\n.BI %s\n' % opt_str.replace('=', '= '))

        if option.help:
            help_text = '%s\n' % self.expand_default(option)
            result.append(self._markup(help_text))

        return ''.join(result)


build.sub_commands.append(('build_manpage', None))
clean.sub_commands.append(('clean_manpage', None))

setup(
    name='python-fll',
    author='Kel Modderman',
    author_email='kel@otaku42.de',
    license='GPL-2',
    description='FULLSTORY live linux media python utility and modules',
    url='http://developer.berlios.de/projects/fullstory/',
    packages=['fll'],
    scripts=['bin/fll'],
    data_files=[
        ('/usr/share/fll/data', ['data/locales-pkg-map']),
        ('/usr/share/fll', ['data/fullstory.py']),
    ],
    cmdclass={
        'build_manpage': build_manpage,
        'clean_manpage': clean_manpage,
        'clean': clean_with_subcommands,
    }
)
