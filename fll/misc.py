import shlex
import signal
import subprocess

def restore_sigpipe():
    """Convenience function so that subprocess may be executed with
    SIGPIPE restored to default (http://bugs.python.org/issue1652)."""
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)

def cmd(cmd, pipe=False):
    """Execute a command."""
    if isinstance(cmd, str):
        cmd = shlex.split(cmd)

    if pipe:
        proc = subprocess.Popen(cmd, preexec_fn=restore_sigpipe,
                                stdout=subprocess.PIPE)
    else:
        proc = subprocess.Popen(cmd, preexec_fn=restore_sigpipe)
    proc.wait()

    if pipe:
        return proc.returncode, proc.communicate()[0]
    else:
        return proc.returncode
