import io
import sys

# def redirect_output(func, *args):
#     '''Redirect the output from a third party function into a string'''

#     buffer = io.StringIO()
#     sys.stdout = buffer

#     result = func(*args)

#     sys.stdout = sys.__stdout__
#     return result, buffer.getvalue()

def foo():
    print('hello from python')

# result, output = redirect_output(foo)
# print(output, end = '')

import os
from contextlib import contextmanager

@contextmanager
def stdout_redirected(to=os.devnull):
    '''
    import os

    with stdout_redirected(to=filename):
        print("from Python")
        os.system("echo non-Python applications are also supported")
    '''
    fd = sys.stdout.fileno()

    ##### assert that Python and C stdio write using the same file descriptor
    ####assert libc.fileno(ctypes.c_void_p.in_dll(libc, "stdout")) == fd == 1

    def _redirect_stdout(to):
        sys.stdout.close() # + implicit flush()
        os.dup2(to.fileno(), fd) # fd writes to 'to' file
        sys.stdout = os.fdopen(fd, 'w') # Python writes to fd

    with os.fdopen(os.dup(fd), 'w') as old_stdout:
        with open(to, 'w') as file:
            _redirect_stdout(to=file)
        try:
            yield # allow code to be run with the redirected stdout
        finally:
            _redirect_stdout(to=old_stdout) # restore stdout.
                                            # buffering and flags such as
                                            # CLOEXEC may be different

with stdout_redirected(to = 'foo.txt'):
    foo()
    print('hello from python2')
    os.system("echo hello from bash")
    print('hello from python3')
    
    

# foo()