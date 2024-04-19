import sys

# tell python where compiled miniscope module is installed
sys.path.append('/lib/python3.10/dist-packages/')
from miniscope import Miniscope, ControlKind

def setup_miniscope(m, miniscope_name, daq_id):
    '''take a freshly instantiated miniscope 'm', run some setup diagnostics on it, and get it running'''

    # disable some debug/info messages about data transmission
    # to make the console output of this example easier to read
    m.set_print_extra_debug(False)

    # list all available miniscope types
    print('Available Miniscope hardware types:')
    for dname in m.available_device_types:
        print(' * {}'.format(dname))

    print()
    print('Selecting: {}'.format(miniscope_name))
    if not m.load_device_config(miniscope_name):
        print('Unable to load device configuration for {}: {}'.format(miniscope_name, m.last_error),
            file=sys.stderr)
        sys.exit(1)

    print('Available controls:')
    controls = {}
    for ctl in m.controls:
        controls[ctl.id] = ctl
        value_start = ctl.value_start
        if ctl.kind == ControlKind.SELECTOR:
            default_val = value_start
            if int(value_start) < len(ctl.labels):
                # replace the number with a human-readable string´
                default_val = ctl.labels[int(value_start)]
            print(' * {}: {} (default value: {})'.format(ctl.id, ctl.name, default_val))
        else:
            print(' * {}: {} (default value: {})'.format(ctl.id, ctl.name, value_start))

    print('Connecting to device with ID: {}\n'.format(daq_id))
    m.set_cam_id(daq_id)
    if not m.connect():
        print('Unable to connect to Miniscope: {}'.format(m.last_error), file=sys.stderr)
        sys.exit(1)

    if not m.run():
        print('Unable to start data acquisition: {}'.format(m.last_error), file=sys.stderr)
        sys.exit(1)