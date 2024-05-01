import sys
import io

import logging
logger = logging.getLogger(__name__)

# tell python where compiled miniscope module is installed
sys.path.append('/lib/python3.10/dist-packages/')
from miniscope import Miniscope, ControlKind

def redirect_output(func, *args):
    '''Redirect the output from a third party function into a string'''

    buffer = io.StringIO()
    sys.stdout = buffer

    result = func(*args)

    sys.stdout = sys.__stdout__
    return result, buffer.getvalue()

def setup_miniscope(m, miniscope_name, daq_id):
    '''Take a freshly instantiated miniscope 'm', run some setup diagnostics on it, and get it running'''

    # disable some debug/info messages about data transmission
    # to make the console output of this example easier to read
    m.set_print_extra_debug(False)

    # remove BNO indicator icon from recorded images
    m.bno_indicator_visible = False

    logger.info('Selecting Miniscope: {}'.format(miniscope_name))
    if not m.load_device_config(miniscope_name):
        logger.error('Unable to load device configuration for {}: {}'.format(miniscope_name, m.last_error),
            file=sys.stderr)
        sys.exit(1)

    logger.info('Connecting to DAQ with ID: {}'.format(daq_id))
    result, output = redirect_output(m.set_cam_id, daq_id)
    # logger.info(output)

    # connect to miniscope
    result, output = redirect_output(m.connect)
    # logger.info(output)
    if not result:
        logger.error('Unable to connect to Miniscope: {}'.format(m.last_error), file=sys.stderr)
        sys.exit(1)

    # run miniscope
    result, output = redirect_output(m.run)
    # logger.info(output)
    if not result:
        logger.error('Unable to start data acquisition: {}'.format(m.last_error), file=sys.stderr)
        sys.exit(1)