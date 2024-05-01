import io
import sys

def redirect_output(func, *args):
    '''Redirect the output from a third party function into a string'''

    buffer = io.StringIO()
    sys.stdout = buffer

    result = func(*args)

    sys.stdout = sys.__stdout__
    return result, buffer.getvalue()

def foo():
    print('hello world')

result, output = redirect_output(foo)
print(output, end = '')