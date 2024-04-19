#!/usr/bin/env python3

# script to run the miniscope in time-lapse mode, adapted from example.py

import time
import sys
import cv2

# tell python where compiled miniscope module is installed
sys.path.append('/lib/python3.10/dist-packages/')
from miniscope import Miniscope, ControlKind

MINISCOPE_DEVICE = 'Miniscope_V4_BNO'  # The device type we want to connect to
DEVICE_ID = 0  # the video device ID of our DAQ box
VIDEO_FILENAME = '/mnt/c/Users/agroo/niko_miniscope_vids/miniscope-test.mkv'

# create new Miniscope instance
mscope = Miniscope()

# disable some debug/info messages about data transmission
# to make the console output of this example easier to read
mscope.set_print_extra_debug(False)

# list all available miniscope types
print('Available Miniscope harware types:')
for dname in mscope.available_device_types:
    print(' * {}'.format(dname))

print()
print('Selecting: {}'.format(MINISCOPE_DEVICE))
if not mscope.load_device_config(MINISCOPE_DEVICE):
    print('Unable to load device configuration for {}: {}'.format(MINISCOPE_DEVICE, mscope.last_error),
          file=sys.stderr)
    sys.exit(1)

print('Available controls:')
controls = {}
for ctl in mscope.controls:
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

print('Connecting to device with ID: {}\n'.format(DEVICE_ID))
mscope.set_cam_id(DEVICE_ID)
if not mscope.connect():
    print('Unable to connect to Miniscope: {}'.format(mscope.last_error), file=sys.stderr)
    sys.exit(1)

if not mscope.run():
    print('Unable to start data acquisition: {}'.format(mscope.last_error), file=sys.stderr)
    sys.exit(1)

def set_led(m, val):
    '''Set the LED on the miniscope 'm' to the value 'val' (0-100).'''
    if 0 <= val <= 100:
        time.sleep(1)
        print('Setting excitation control to {}'.format(val))
        m.set_control_value('led0', val)
        time.sleep(1)
    else:
        print("Please input a value between 0 and 100.")

# prepare video recording
print('\n--------')
print('Codec used for recording: {}'.format(mscope.video_codec))
print('Container used for recording: {}'.format(mscope.video_container))
print('Saving video in: {}'.format(VIDEO_FILENAME))
print('--------\n')

# time lapse loop
nsnapshots = 0
while nsnapshots < 10:
    # turn the LED on
    set_led(mscope, 20)

    # start recording
    if not mscope.start_recording(VIDEO_FILENAME):
        print('Unable to start video recording: {}'.format(mscope.last_error), file=sys.stderr)
        sys.exit(1)
    # record a small number of frames
    nframes = 0
    while nframes < 5:
        frame = mscope.current_disp_frame
        if frame is not None:
            cv2.imshow('Miniscope Display', frame)
            cv2.waitKey(50)
            nframes += 1
    
    # turn the LED off
    set_led(mscope, 0)

    # wait 5 seconds for next snapshot
    nsnapshots += 1
    time.sleep(5)
    
set_led(mscope, 0)
mscope.stop()

if mscope.last_error:
    print('Error while acquiring data from Miniscope: {}'.format(mscope.last_error), file=sys.stderr)

mscope.disconnect()
cv2.destroyAllWindows()
