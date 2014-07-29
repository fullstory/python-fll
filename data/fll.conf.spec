##############################################################################
# Build architecture(s). Specify which architectures you would like to
# bootstrap and build for. Multiple architectures must be separated by
# a comma. Defaults to host architecture.
#
# Can be set via --archs <ARCH>[ <ARCH> ...] command line argument.
#
archs		= list(default=list())

# The Debian mirror. config['apt']['sources']['debian']['uri'] and
# config['chroot']['bootstrap']['uri'] default to this ($mirror). Either that
# or comment this out and set those configuration items independently.
#
# Can be set via --mirror=<MIRROR> command line argument.
#
mirror		= string(min=1, default='http://cdn.debian.net/debian/')

# Build directory. A large amount of freespace is required. The mountpoint
# where this directory exists must be mounted with permissive options as you
# would expect for a (ch)root filesystem or the build _will_ fail. Defaults
# to current working directory.
#
# Can be set via --dir=<DIR> command line argument.
#
dir		= string(min=1, default='.')

# UID and GID of output files.
#
# Can be set via --uid <UID> and --gid <GID> respectively.
#
uid		= integer(default=0)
gid		= integer(default=0)

# Dry run mode. Do not perform time consuming processes.
#
# Can be set via --dry-run command line argument.
#
dryrun		= boolean(default=False)

# quiet / verbose / debug modes. Default is quiet.
#
# Can be set via --quiet, --verbose, --debug command line arguments.
#
verbosity	= option('quiet', 'verbose', 'debug', default='quiet')

__many__	= string(min=1)

##############################################################################
# HTTP/FTP Proxy setup. When set [apt][[conf]][[[Acquire::http::Proxy]]] and
# [environment][[http_proxy]] will inherit its value. Ditto for ftp_proxy.
#
# Can be set via --http-proxy=<PROXY> and --ftp-proxy=<PROXY> command line
# arguments.
#
[network]
[[ftp]]
proxy		= string(default='')
[[http]]
proxy		= string(default='')

##############################################################################
# General options for fll.aptlib.AptLib class.
#
[apt]

# Fetch source packages and create archive of software installed in chroot
# filesystems.
#
# Can be set via --apt-src command line argument.
#
src		= boolean(default=False)

# Verbosity level of class. Inherits the top level 'verbosity' mode.
#
# Can be set via --apt-quiet, --apt-verbose and --apt-debug command line
# arguments.
#
quiet		= boolean(default=False)
verbose		= boolean(default=False)
debug		= boolean(default=False)


[[key]]
# Toggle for trust verification of apt sources. By default apt will verify
# that each package comes from an origin whose Release file has been gpg
# signed, and a pubkey for it exists in the trusted keyring.
#
# Can be set via --apt-key-disable command line argument.
#
disable		= boolean(default=False)

# Keyserver URI to receive gpg key(s) from.
#
# Can be set via --apt-key-server <KEYSERVER> command line argument.
#
server		= string(min=1, default='wwwkeys.eu.pgp.net')

# Each entry in the [apt][[conf]] section is an apt configuration
# keyword=value pair.
#
# Can be set via the --apt-conf <KEYWORD=VALUE>[ <KEYWORD=VALUE> ...]
# command line argument.
#
# See /usr/share/doc/apt/examples/configure-index.gz for a full list of apt
# configuration examples. Dir (alias RootDir) and Architecture are handled by
# the fll.apt.Apt class. Acquire::http::Proxy and Acquire::ftp::Proxy are
# configured via [network][[http]][[[proxy]]] and [network][[fttp]][[[proxy]]]
[[conf]]
__many__	= string(min=1)

# The [apt][[sources]] section can contain several subsections which describe
# Debian package apt repositories.
#
# Can be set via the --apt-source command line argument.
#
# Each subsection contains information for an individual apt repository. It
# must include description, uri, suite and component fields. The name of
# the subsection (ie. the quoted string between [[[ and ]]]) is used as the
# filename for the apt sources list (eg. /etc/apt/sources.list.d/<name>.list).
#
# Fields:-
# description - One line description of repository.
# uri         - Debian repository URI (aka Debian mirror). This URI is used
#               throughout the bootstrap and build components of the build
#               process. Debian package caching is recommended with tools such
#               as approx or apt-cacher-ng.
# final_uri   - This URI is published to the sources.list snippet at the final
#               stages of the build process. If ommitted, $uri is used.
# suite       - Suite name(s) (eg. "sid," or "sid,experimental").
# components  - Repository components (eg. "main," or "main,contrib,non-free").
# keyring     - Name of package containing gpg key required for authentication
# gpgkey      - 8 character gpg keyid fetchable from keyserver
#		or
#		absolute filename to exported public key
#		or
#		http/ftp URI to exported public key
[[sources]]

# The Debian repository
[[[debian]]]
description	= string(min=1, default='Debian GNU/Linux')
uri		= string(min=1, default='$mirror')
final_uri	= string(default='')
suites		= list(default=list('sid'))
components	= list(default=list('main'))

[[[__many__]]]
description	= string(default='')
uri		= string(default='')
final_uri	= string(min=1, default=None)
suites		= list(default=list('sid'))
components	= list(default=list('main'))
keyring		= string(default='')
gpgkey		= string(default='')

##############################################################################
# General options for fll.pkgmod.PkgMod class.
#
[profile]

# Name of the package profile to parse
name		= string(default='')

# Path to package module directory
dir		= string(default='')

# Packages to be installed
packages	= list(default=list())


##############################################################################
# General options for fll.chroot.Chroot class.
#
[chroot]

# Preserve the chroot filesystems after build process. Default is to remove
# them. It may be beneficial to preserve them for debugging purposes, but they
# cannot be modified and reused as that is abortive ugly nonsense.
#
# Can be set via the --chroot-preserve command line argument.
#
preserve	= boolean(default=False)

# Verbosity level of class. Inherits the top level 'verbosity' mode.
#
# Can be set via --chroot-quiet, --chroot-verbose and --chroot-debug command
# line arguments.
#
quiet		= boolean(default=False)
verbose		= boolean(default=False)
debug		= boolean(default=False)

# Hostname for the chroot.  Defaults to chroot
#
# Can be set via --hostname
hostname       = string(min=1, default="chroot")

# Bootstrap utility and options.
#
# For every keyword=value pair below exists a command line argument:
# --chroot-<KEYWORD> <VALUE>
#
[[bootstrap]]
utility		= option('cdebootstrap', 'debootstrap', default='cdebootstrap')
suite		= string(min=1, default='sid')
uri		= string(min=1, default='$mirror')
flavour		= option('minimal', 'build', 'standard', default='minimal')
include		= string(default='apt-utils,bzip2,gnupg,systemd-sysv,xz-utils')
exclude		= string(default='init,sysvinit,sysvinit-core')

##############################################################################
# Each entry in this section is an environment variable keyword=value pair.
#
# Can be set via the --environment <KEYWORD=VALUE>[ <KEYWORD=VALUE> ...]
# command line argument.
#
[environment]
PATH		= string(min=1, default='/usr/sbin:/usr/bin:/sbin:/bin')
HOME		= string(min=1, default='/root')
SHELL		= string(min=1, default='/bin/bash')
LANGUAGE	= string(min=1, default='C')
LC_ALL		= string(min=1, default='C')
LANG		= string(min=1, default='C')
DEBIAN_FRONTEND	= string(min=1, default='noninteractive')
DEBIAN_PRIORITY	= string(min=1, default='critical')
__many__	= string(min=1)

##############################################################################
# Each entry in this section is an distro variable keyword=value pair.
#
# Can be set via the --distro <KEYWORD=VALUE>[ <KEYWORD=VALUE> ...]
# command line argument.
#
[distro]
__many__	= string(min=1)

##############################################################################
# General options for fll.fscomp.FsComp class.
#
[fscomp]

# Type of compression to use for chroot filesystem "image". Not much choice
# atm :) Each choice should have a subsection below.
#
compression	= option('none', 'squashfs', 'tar', default='none')

# Verbosity level of class. Inherits the top level 'verbosity' mode.
#
# Can be set via --fsimage-quiet, --fsimage-verbose and --fsimage-debug
# command line arguments.
#
quiet		= boolean(default=False)
verbose		= boolean(default=False)
debug		= boolean(default=False)

# Squashfs compression options.
#
[[squashfs]]
# gzip, lzo or xz compressor
compressor	= option('gzip', 'lzo', 'xz', default='gzip')

# Tar compression options.
#
[[tar]]
# gz, bz, xz or pixz compressor
compressor	= option('gz', 'bz', 'xz', 'pz', default='gz')

##############################################################################
# Boot loader related options.
#
[boot]
# grub or syslinux
loader		= option('grub', 'syslinux', default='grub')
# Default timeout period before booting default entry
timeout		= integer(default='30')
# Default kernel command line parameters
cmdline		= string(default='quiet')
