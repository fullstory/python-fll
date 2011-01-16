#!/usr/bin/python

from distutils.command.build import build
from distutils.command.clean import clean
from distutils.core import setup, Command
from distutils.errors import DistutilsOptionError
import datetime
import os


MAN = {
    'fll.8': {
        'module': 'fll.cmdline',
        'function': 'cmdline',
        'command': 'fll',
        'section': 8,
        'authors': ['Kel Modderman <kel@otaku42.de>'],
        'files': ['/etc/fll/fll.conf'],
        'see_also': ['apt.conf(5)', 'apt-secure(8)',
                     'debconf(7)', 'cdeboostrap(8)'],
        },
    }

class clean_with_subcommands(clean):
    def run(self):
        for cmd_name in self.get_sub_commands():
            self.run_command(cmd_name)
        clean.run(self)

class clean_manpages(Command):
    description = 'Remove manual pages from setup().'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        for man in MAN.iterkeys():
            if os.path.isfile(man):
                os.unlink(man)

class build_manpages(Command):
    description = 'Generate manual pages from setup().'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        for man, maninfo in MAN.iteritems():
            self._gen_man(man, maninfo)

    def _gen_man(self, man, maninfo):
        def markup(txt):
            return txt.replace('-', '\\-')

        today = datetime.date.today().strftime('%Y-%m-%d')
        command = maninfo.get('command')
        section = maninfo.get('section')
        module = maninfo.get('module')
        function = maninfo.get('function')
        authors = maninfo.get('authors')
        copyright = maninfo.get('copyright')
        files = maninfo.get('files')
        see_also = maninfo.get('see_also')

        mod = __import__(module, fromlist=module.split('.'))
        parser = getattr(mod, function)()

        help = parser.format_help().splitlines()
        usage = parser.format_usage().splitlines()

        desc_start = len(usage) + 1
        desc_end = opts_start = 0
        for n, line in enumerate(help):
            if line.startswith('positional arguments:') or \
               line.startswith('optional arguments:'):
                desc_end = n - 1
                opts_start = n
        desc = help[desc_start:desc_end]
        opts = help[opts_start:]

        fh = open(man, 'w')

        fh.write(markup('.TH %s %d %s\n' % (command, section, today)))

        short_desc = desc[0].rstrip('.')
        fh.write('.SH NAME\n')
        fh.write(markup('%s - %s\n' % (command, short_desc)))

        long_desc = desc[2:]
        fh.write('.SH DESCRIPTION\n')
        for line in long_desc:
            line = line.strip()
            if line == '':
                line = '.PP'
            if line.startswith('* '):
                line = line.replace('* ', '.IP \\(bu\n')
            if line.startswith('$ '):
                line = line.replace('$ ', '.IP \\(bu\n')
            if line.startswith('Examples:'):
                line = line.strip(':')
                line = '.SH ' + line.upper()
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
            if line.endswith('arguments:'):
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
            elif line == '':
                pass
            else:
                fh.write('%s\n' % markup(line))

        if files:
            fh.write('.SH FILES\n')
            for f in sorted(files):
                fh.write('.IP \\(bu\n%s\n' % markup(f))

        if see_also:
            fh.write('.SH SEE ALSO\n')
            see_also.sort()
            line = markup(', '.join(see_also))
            line = line.replace('(', ' "(')
            line = line.replace('),', '), " ')
            fh.write('.BR %s"\n' % line)

        fh.write('.SH AUTHORS\n')
        fh.write('%s\n' % markup(', '.join(authors)))

        fh.write('.SH COPYRIGHT\n')
        fh.write('Copyright \(co %s %s.\n' %
                 (today.split('-')[0], authors[0]))

        fh.close()


build.sub_commands.append(('build_manpages', None))
clean.sub_commands.append(('clean_manpages', None))

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
        'build_manpages': build_manpages,
        'clean_manpages': clean_manpages,
        'clean': clean_with_subcommands,
    }
)
