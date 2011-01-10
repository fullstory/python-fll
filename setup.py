#!/usr/bin/python

from distutils.command.build import build
from distutils.command.clean import clean
from distutils.core import setup, Command
from distutils.errors import DistutilsOptionError
import datetime
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

    def run(self):
        def markup(txt):
            return txt.replace('-', '\\-')

        author = self.distribution.get_author()
        email = self.distribution.get_author_email()
        homepage = self.distribution.get_url()
        today = datetime.date.today().strftime('%Y-%m-%d')
        command = self.output.split('.')[0]
        section = self.output.split('.')[-1]

        help = self.parser.format_help().splitlines()
        usage = self.parser.format_usage().splitlines()

        desc_start = len(usage) + 1
        desc_end = opts_start = 0
        for n, line in enumerate(help):
            if line.startswith('positional arguments:') or \
               line.startswith('optional arguments:'):
                desc_end = n - 1
                opts_start = n
        desc = help[desc_start:desc_end]
        opts = help[opts_start:]

        fh = open(self.output, 'w')

        fh.write(markup('.TH %s %s %s\n' % (command, section, today)))

        short_desc = desc[0].rstrip('.')
        fh.write('.SH NAME\n')
        fh.write(markup('%s - %s\n' % (command, short_desc)))

        long_desc = desc[2:]
        fh.write('.SH DESCRIPTION\n')
        for line in long_desc:
            line = line.strip()
            if len(line) == 0:
                line = '.PP'
            if line.startswith('* '):
                line = line.replace('* ', '.IP \\(bu\n')
            fh.write('%s\n' % markup(line))

        fh.write('.SH SYNOPSIS\n')
        fh.write('.B %s' % markup(command))
        for line in usage:
            line = line.strip()
            if line.startswith('usage:'):
                line = line.replace('usage: ', '')
            if line.startswith(command):
                line = line.replace('%s ' % command, '')
            line = line.replace('[', ' [ ')
            line = line.replace(']', ' ] ')
            for word in line.split():
                if word in ['[', ']', '|']:
                    fh.write('\n%s' % word)
                elif word.startswith('-'):
                    fh.write('\n.B %s' % markup(word))
                else:
                    fh.write('\n.I %s' % markup(word))
        fh.write('\n')

        fh.write('.SH OPTIONS\n')
        for line in opts:
            line = line.strip()
            if line.startswith('positional arguments:') or \
               line.startswith('optional arguments:'):
                line = line.rstrip(':')
                line = line.upper()
                fh.write('.SS %s\n' % line)
            elif line.startswith('-'):
                fh.write('.TP\n')
                for part in line.split('  '):
                    part = part.strip()
                    part = part.replace(', -', ' ", " -')
                    part = part.replace('[', ' [ ')
                    part = part.replace(']', ' ] ')
                    if part == '':
                        continue
                    elif part.startswith('-'):
                        fh.write('.BR')
                        for word in part.split():
                            if word.startswith('<') or word == '...':
                                fh.write(' " " \\fI%s' % markup(word))
                            elif word in ['[', ']']:
                                fh.write(' \\fR%s' % word)
                            else:
                                fh.write(' %s' % markup(word))
                        fh.write('\n')
                    else:
                        fh.write('%s\n' % markup(part))
            else:
                fh.write('%s\n' % markup(line))

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
            fh.write('The latest info about \\fB%s\\fR is at\n' % markup(command))
            fh.write('.UR %s\n.UE .\n' % markup(homepage))

        if author and author != 'UNKNOWN':
            fh.write('.SH AUTHORS\n')
            fh.write('%s\n' % markup(author))

            if email and email != 'UNKNOWN':
                fh.write('.UR %s\n.UE .\n' % markup(email))

            fh.write('.SH COPYRIGHT\n')
            fh.write('Copyright \(co %s %s.\n' %
                     (today.split('-')[0], markup(author)))

        fh.close()


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
        ('/usr/share/fll', ['conf/fll.conf.spec']),
    ],
    cmdclass={
        'build_manpage': build_manpage,
        'clean_manpage': clean_manpage,
        'clean': clean_with_subcommands,
    }
)
