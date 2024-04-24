import sys

# tell python where compiled miniscope module is installed
sys.path.append('/lib/python3.10/dist-packages/')
from miniscope import Miniscope, ControlKind

def setup_miniscope(m, miniscope_name, daq_id):
    '''take a freshly instantiated miniscope 'm', run some setup diagnostics on it, and get it running'''

    # disable some debug/info messages about data transmission
    # to make the console output of this example easier to read
    m.set_print_extra_debug(False)

    print('Selecting Miniscope: {}'.format(miniscope_name))
    if not m.load_device_config(miniscope_name):
        print('Unable to load device configuration for {}: {}'.format(miniscope_name, m.last_error),
            file=sys.stderr)
        sys.exit(1)

    print('Connecting to DAQ with ID: {}\n'.format(daq_id))
    m.set_cam_id(daq_id)

    # connect to miniscope
    if not m.connect():
        print('Unable to connect to Miniscope: {}'.format(m.last_error), file=sys.stderr)
        sys.exit(1)

    # run miniscope
    if not m.run():
        print('Unable to start data acquisition: {}'.format(m.last_error), file=sys.stderr)
        sys.exit(1)