import signal

def restore_sigpipe():
    """Convenience function so that subprocess may be executed with
    SIGPIPE restored to default (http://bugs.python.org/issue1652)."""
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
