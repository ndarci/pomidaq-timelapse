import sys
import os
import io
from contextlib import contextmanager

def redirect_output(func, *args):
    '''Redirect the output from a third party function into a string'''
    buffer = io.StringIO()
    sys.stderr = buffer
    result = func(*args)
    sys.stderr = sys.__stderr__
    return result, buffer.getvalue()

@contextmanager
def stderr_redirected(to=os.devnull):
    '''
    import os

    with stderr_redirected(to=filename):
        print("from Python")
        os.system("echo non-Python applications are also supported")
    '''
    fd = sys.stderr.fileno()

    ##### assert that Python and C stdio write using the same file descriptor
    ####assert libc.fileno(ctypes.c_void_p.in_dll(libc, "stdout")) == fd == 1

    def _redirect_stderr(to):
        sys.stderr.close() # + implicit flush()
        os.dup2(to.fileno(), fd) # fd writes to 'to' file
        sys.stderr = os.fdopen(fd, 'w') # Python writes to fd

    with os.fdopen(os.dup(fd), 'w') as old_stderr:
        with open(to, 'w') as file:
            _redirect_stderr(to=file)
        try:
            yield # allow code to be run with the redirected stdout
        finally:
            _redirect_stderr(to=old_stderr) # restore stderr
                                            # buffering and flags such as
                                            # CLOEXEC may be different
