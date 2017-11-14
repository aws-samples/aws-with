"""
    monkey patches to cover python 2.6 gaps
    see: https://stackoverflow.com/questions/...
            .../4814970/subprocess-check-output-doesnt-seem-to-exist-python-2-6-5
"""

import subprocess

def apply_patches():
    """ apply monkey patches if required """
    patch_subprocess()

def patch_subprocess():
    """ patch in subprocess.check_output() function if it is missing """

    if hasattr(subprocess, "check_output"):
        return
    else:
        subprocess.check_output = ___subprocess_check_output
        subprocess.CalledProcessError = CalledProcessError

def ___subprocess_check_output(*popenargs, **kwargs):
    """ backwards compatible check_output function for old versions of Python """
    if 'stdout' in kwargs:  # pragma: no cover
        raise ValueError('stdout argument not allowed, '
                         'it will be overridden.')
    process = subprocess.Popen(stdout=subprocess.PIPE,
                               *popenargs, **kwargs)
    output, _ = process.communicate()
    retcode = process.poll()
    if retcode:
        cmd = kwargs.get("args")
        if cmd is None:
            cmd = popenargs[0]
        raise subprocess.CalledProcessError(retcode, cmd,
                                            output=output)
    return output

class CalledProcessError(Exception):
    """ exception class to carry exec error details """

    def __init__(self, returncode, cmd, output=None):
        Exception.__init__(self)
        self.returncode = returncode
        self.cmd = cmd
        self.output = output

    def __str__(self):
        return "Command '%s' returned non-zero exit status %d" % (
            self.cmd, self.returncode)
