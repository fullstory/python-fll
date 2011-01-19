import shlex
import signal
import subprocess
import os
import pprint
import sys

def debug(mode, title, obj):
    if mode is False:
        return
    print >>sys.stderr, 'DEBUG BEGIN >>> %s' % title
    if isinstance(obj, str):
        print >>sys.stderr, obj
    else:
        pprint.pprint(obj, sys.stderr, 4)
    print >>sys.stderr, 'DEBUG END   <<< %s' % title

def restore_sigpipe():
    """Convenience function so that subprocess may be executed with
    SIGPIPE restored to default (http://bugs.python.org/issue1652)."""
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)

def cmd(cmd, pipe=False, quiet=False, silent=False):
    """Execute a command."""
    if isinstance(cmd, str):
        cmd = shlex.split(cmd)

    if silent is False:
        print 'HOST %s' % ' '.join(cmd)

    devnull = output = None

    try:
        if pipe:
            proc = subprocess.Popen(cmd, preexec_fn=restore_sigpipe,
                                    stdout=subprocess.PIPE)
            output = proc.communicate()[0]
        elif quiet or silent:
            devnull = os.open(os.devnull, os.O_RDWR)
            proc = subprocess.Popen(cmd, preexec_fn=restore_sigpipe,
                                    stdout=devnull)
            proc.wait()
        else:
            proc = subprocess.Popen(cmd, preexec_fn=restore_sigpipe)
            proc.wait()
    except OSError, e:
        raise OSError('command failed: %s' % e)
    finally:
        if devnull:
            os.close(devnull)

    if proc.returncode != 0:
        raise OSError('command returncode=%d: %s' % \
                      (proc.returncode, ' '.join(cmd)))

    if pipe:
        return output
