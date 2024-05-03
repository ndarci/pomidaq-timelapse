MINISCOPE_NAME = 'Miniscope_V4_BNO'  # the device type we want to connect to
DAQ_ID = 0  # the video device ID of our DAQ box

import io
import sys
import os

import logging
logger = logging.getLogger(__name__)

from contextlib import redirect_stderr, redirect_stdout

# tell python where compiled miniscope module is installed
sys.path.append('/lib/python3.10/dist-packages/')
from miniscope import Miniscope, ControlKind

def redirect_output(func, *args, **kwargs):
# def redirect_output(func):
    '''Redirect the output from a third party function into a string'''

    buffer = io.StringIO()
    sys.stderr = buffer

    result = func(*args, **kwargs)
    # func()
    # print('foo', file = sys.stderr)

    sys.stderr = sys.__stderr__
    return result, buffer.getvalue()




# def printfoo(msg):
#     print(msg, file = sys.stderr)

# # result, output = redirect_output(print, 'foo', file = sys.stderr)
# print('this should be silenced:', file = sys.stderr)
# redirect_output(printfoo, 'hello')
# redirect_output(print, 'foo', file = sys.stderr)
# print('this should be printed:', file = sys.stderr)
# printfoo('hello')

with io.StringIO() as buffer, redirect_stderr(buffer):
    print('hello from stdout', file = sys.stdout)
    print('hello from stderr', file = sys.stderr)
    output = buffer.getvalue()

print('redirected output: ' + output)

miniscope_name = MINISCOPE_NAME
daq_id = DAQ_ID

m = Miniscope()

m.set_print_extra_debug(False)

# remove BNO indicator icon from recorded images
m.bno_indicator_visible = False

logger.info('Selecting Miniscope: {}'.format(miniscope_name))
if not m.load_device_config(miniscope_name):
    logger.error('Unable to load device configuration for {}: {}'.format(miniscope_name, m.last_error),
        file=sys.stderr)
    sys.exit(1)

logger.info('Connecting to DAQ with ID: {}'.format(daq_id))

m.set_cam_id(daq_id)

# connect to miniscope
# with io.StringIO() as buffer, redirect_stderr(buffer):
#     result = m.connect()
#     output = buffer.getvalue()

result, output = redirect_output(m.connect)

print('result: ' + str(result))
print('output: ' + output)


if not result:
    logger.error('Unable to connect to Miniscope: {}'.format(m.last_error), file=sys.stderr)
    sys.exit(1)

# run miniscope
result = m.run()
if not result:
    logger.error('Unable to start data acquisition: {}'.format(m.last_error), file=sys.stderr)
    sys.exit(1)



# def foo():
#     print('hello from python')

# # result, output = redirect_output(foo)
# # print(output, end = '')

# import os
# from contextlib import contextmanager

# @contextmanager
# def stdout_redirected(to=os.devnull):
#     '''
#     import os

#     with stdout_redirected(to=filename):
#         print("from Python")
#         os.system("echo non-Python applications are also supported")
#     '''
#     fd = sys.stdout.fileno()

#     ##### assert that Python and C stdio write using the same file descriptor
#     ####assert libc.fileno(ctypes.c_void_p.in_dll(libc, "stdout")) == fd == 1

#     def _redirect_stdout(to):
#         sys.stdout.close() # + implicit flush()
#         os.dup2(to.fileno(), fd) # fd writes to 'to' file
#         sys.stdout = os.fdopen(fd, 'w') # Python writes to fd

#     with os.fdopen(os.dup(fd), 'w') as old_stdout:
#         with open(to, 'w') as file:
#             _redirect_stdout(to=file)
#         try:
#             yield # allow code to be run with the redirected stdout
#         finally:
#             _redirect_stdout(to=old_stdout) # restore stdout.
#                                             # buffering and flags such as
#                                             # CLOEXEC may be different

# with stdout_redirected(to = 'foo.txt'):
#     foo()
#     print('hello from python2')
#     os.system("echo hello from bash")
#     print('hello from python3')
    
    

# # foo()