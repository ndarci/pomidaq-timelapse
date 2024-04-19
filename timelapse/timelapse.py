#!/usr/bin/env python3

# script to run the miniscope in time-lapse mode, adapted from example.py

import time
import sys
import cv2

# tell python where compiled miniscope module is installed
sys.path.append('/lib/python3.10/dist-packages/')
from miniscope import Miniscope, ControlKind

from mscopesetup import setup_miniscope
from mscopecontrol import set_led, set_focus, set_gain

MINISCOPE_DEVICE = 'Miniscope_V4_BNO'  # The device type we want to connect to
DEVICE_ID = 0  # the video device ID of our DAQ box
VIDEO_FILENAME = '/mnt/c/Users/agroo/niko_miniscope_vids/miniscope-test.mkv' # video file location

def print_recording_info(m):
    '''output encoding format for miniscope 'm' and video file location'''
    print('\n--------')
    print('Codec used for recording: {}'.format(m.video_codec))
    print('Container used for recording: {}'.format(m.video_container))
    print('Saving video in: {}'.format(VIDEO_FILENAME))
    print('--------\n')

def shoot_timelapse(m, total_snapshots = 10, frames_per_snapshot = 5, period_sec = 5):
    print_recording_info(m)

    # just shoot video for 5 seconds for now
    set_led(m, 20)
    if not m.start_recording(VIDEO_FILENAME):
        print('Unable to start video recording: {}'.format(m.last_error), file=sys.stderr)
        sys.exit(1)

    time.sleep(5)

    # stop recording i think?? need to check what this does
    m.stop()

    # verify that LED is turned off before function returns 
    set_led(m, 0)



    # # time lapse loop
    # nsnapshots = 0
    # while nsnapshots < total_snapshots:
    #     # turn the LED on
    #     set_led(m, 20)

    #     # start recording
    #     if not m.start_recording(VIDEO_FILENAME):
    #         print('Unable to start video recording: {}'.format(m.last_error), file=sys.stderr)
    #         sys.exit(1)

    #     # record a small number of frames
    #     nframes = 0
    #     while nframes < frames_per_snapshot:
    #         frame = m.current_disp_frame
    #         if frame is not None:
    #             cv2.imshow('Miniscope Display', frame)
    #             cv2.waitKey(50)
    #             nframes += 1
        
    #     # turn the LED off
    #     set_led(m, 0)

    #     # wait period_sec seconds for next snapshot
    #     nsnapshots += 1
    #     time.sleep(period_sec)

def main():
    # create new Miniscope instance
    mscope = Miniscope()

    # run some diagnostics and start it running
    setup_miniscope(mscope)

    # set initial control levels
    set_led(mscope, 0)
    set_focus(mscope, 0)
    set_gain(mscope, 0)

    # run timelapse loop with input parameters
    shoot_timelapse(mscope)

    # handle errors, if they happened
    if mscope.last_error:
        print('Error while acquiring data from Miniscope: {}'.format(mscope.last_error), file=sys.stderr)

    # disconnect from scope and close cv2 GUI windows
    mscope.disconnect()
    cv2.destroyAllWindows()

    return

if __name__ == '__main__':
    main()
