#!/usr/bin/env python3

# script to run the miniscope in time-lapse mode, adapted from example.py

import time
from datetime import datetime
import os
import sys
import cv2

# tell python where compiled miniscope module is installed
sys.path.append('/lib/python3.10/dist-packages/')
from miniscope import Miniscope, ControlKind

from mscopesetup import setup_miniscope
from mscopecontrol import set_led, set_focus, set_gain

def print_recording_info(m, vid_dir):
    '''Output encoding format and video save directory'''
    print('\n--------')
    print('Codec used for recording: {}'.format(m.video_codec))
    print('Container used for recording: {}'.format(m.video_container))
    print('Saving snapshots to directory: {}'.format(vid_dir))
    print('--------\n')

def shoot_video(m, duration_sec, vidfn):
    '''Shoot a video'''
    if not m.start_recording(vidfn):
        print('Unable to start video recording: {}'.format(m.last_error), file=sys.stderr)
        sys.exit(1)

    time.sleep(duration_sec)

    m.stop_recording()

def shoot_timelapse(m, vid_dir, total_snapshots = 3, snapshot_duration_sec = 5, period_sec = 10):
    '''Shoot a timelapse, which will be a folder full of short video files, to be concatenated afterwards'''
    print_recording_info(m, vid_dir)

    # # just shoot video for 5 seconds for now
    # set_led(m, 20)
    # shoot_video(m, 5)

    # time lapse loop
    print("Starting time lapse recording. Total snapshots=", total_snapshots, ": snapshot duration (sec)=", snapshot_duration_sec, ": period (sec)=", period_sec)
    nsnapshots = 0
    while nsnapshots < total_snapshots:
        print("Taking snapshot", nsnapshots, "...")

        # turn the LED on
        set_led(m, 20)

        # record for a few seconds and write to a file named for the second it started
        # date_sec = datetime.now().strftime("%Y%m%d_%H%M%S")
        # snapshot_filename = 'miniscope_snapshot_' + date_sec + '.mkv'
        snapshot_filename = 'miniscope_snapshot_' + str(nsnapshots) + '.mkv'
        vid_path = os.path.join(vid_dir, snapshot_filename)
        print('video path: ' + vid_path)
        shoot_video(m, snapshot_duration_sec, vid_path)
        
        # turn the LED off
        set_led(m, 0)

        print("Waiting", snapshot_duration_sec, "seconds to take next snapshot ...")
        # wait period_sec seconds for next snapshot
        nsnapshots += 1
        time.sleep(period_sec)

        # foo

    # stop recording and running miniscope
    m.stop()

    print("Time lapse recording finished.")

def main():
    # define key strings for setup and recording
    miniscope_name = 'Miniscope_V4_BNO'  # The device type we want to connect to
    daq_id = 0  # the video device ID of our DAQ box
    # video_filename = '/mnt/c/Users/agroo/niko_miniscope_vids/miniscope-test.mkv' # video file location
    video_dirname = '/home/agroo/niko_miniscope_vids/timelapse_test'
    os.makedirs(video_dirname, exist_ok = True)

    # create new Miniscope instance
    mscope = Miniscope()

    # run some diagnostics and start it running
    setup_miniscope(mscope, miniscope_name, daq_id)

    # set initial control levels
    set_led(mscope, 0)
    set_focus(mscope, 45)
    set_gain(mscope, 0)

    # run timelapse loop with input parameters
    shoot_timelapse(mscope, video_dirname)

    # handle errors, if they happened
    if mscope.last_error:
        print('Error while acquiring data from Miniscope: {}'.format(mscope.last_error), file=sys.stderr)

    # disconnect from scope 
    mscope.disconnect()

    return

if __name__ == '__main__':
    main()
