#!/usr/bin/env python3

# script to run the miniscope in time-lapse mode, adapted from ../py/example.py

# define key strings for setup and recording
MINISCOPE_NAME = 'Miniscope_V4_BNO'  # the device type we want to connect to
DAQ_ID = 0  # the video device ID of our DAQ box
IMAGE_DIRNAME = '/home/agroo/niko_miniscope_vids/timelapse_test' # path to the folder we will store time lapse images in
FFMPEG_PATH = '/home/agroo/src/ffmpeg-git-20240301-amd64-static/ffmpeg' # path to ffmpeg installation

import time
from datetime import datetime
import os
import sys
import cv2
import subprocess

# tell python where compiled miniscope module is installed
sys.path.append('/lib/python3.10/dist-packages/')
from miniscope import Miniscope, ControlKind

from mscopesetup import setup_miniscope
from mscopecontrol import set_led, set_focus, set_gain

def take_photo(m, image_fn, nbuffer_frames = 50):
    '''Take a photo with the Miniscope'''

    # TODO: somehow control for the frames that are all covered in horizontal lines

    # TODO: get rid of little BNO indicator logo in bottom corner

    # it takes a few frames to warm up, throw away the first (nbuffer_frames - 1) frames, then save the last
    nframes = 0
    while m.is_running and nframes < nbuffer_frames:
        frame = m.current_disp_frame
        if frame is not None:
            # cv2.imshow('Miniscope Display', frame)
            # cv2.waitKey(50)
            # print("recorded frame", nframes)
            nframes += 1
    cv2.imwrite(image_fn, frame)

def take_zstack(m, image_dir, snapshot_num, zparams):
    '''Shoot a z-stack of photos with the Miniscope'''

    current_focus = zparams['start']

    while current_focus <= zparams['end']:
        final_image_path = os.path.join(image_dir, 'snapshot' + str(snapshot_num) + '_z' + str(current_focus) + '.jpg')
        set_focus(m, current_focus)
        take_photo(m, final_image_path)
        current_focus += zparams['step']

def shoot_timelapse(m, image_dir, zparams, total_snapshots, period_sec, excitation_strength = 20):
    '''Shoot a timelapse, which will be a folder full of image files, to be concatenated afterwards'''

    print("Starting time lapse recording.")
    print("\tTotal snapshots = " + str(total_snapshots))
    print("\tPeriod (sec) = " + str(period_sec))
    print("\tZ-Stack settings = " + str(zparams))

    nsnapshots = 0
    filenames = [None] * total_snapshots
    # time lapse loop
    while nsnapshots < total_snapshots:
        # turn the LED on
        set_led(m, excitation_strength)

        # take a z-stack at the current state
        print("Taking z-stack " + str(nsnapshots) + " ...")
        take_zstack(m, image_dir, nsnapshots, zparams)
        
        # turn the LED off
        set_led(m, 0)
        
        nsnapshots += 1

        if nsnapshots < total_snapshots:
            print("Waiting", period_sec, "seconds to take next snapshot ...")
            time.sleep(period_sec)

    # stop recording and running miniscope
    m.stop()

    print("Time lapse recording finished.")

    return filenames

def merge_snapshots(vid_dir, vid_fn_list, ffmpeg_path, merged_vid_name):
    '''Use ffmpeg to merge the miniscope snapshots into a single video'''
    # write the list of snapshot filenames to a text file for ffmpeg
    merge_list = open(os.path.join(vid_dir, 'merge_file_names.txt'), 'w')
    merge_list.write('# miniscope snapshots\n')
    for filename in vid_fn_list:
        merge_list.write("file " + "'" + filename + "'\n")
    merge_list.close()
    # call ffmpeg in concat mode on the list of snapshot files
    subprocess.call([ffmpeg_path, '-f', 'concat', '-safe', '0', '-i', os.path.join(vid_dir, 'merge_file_names.txt'), '-c', 'copy', os.path.join(vid_dir, merged_vid_name)])

def main():
    # create new Miniscope instance
    mscope = Miniscope()

    # run some diagnostics and start it running
    setup_miniscope(mscope, MINISCOPE_NAME, DAQ_ID)

    # set initial control levels
    set_led(mscope, 0)
    set_focus(mscope, 0)
    set_gain(mscope, 0)

    # run timelapse loop and save all snapshots
    os.makedirs(IMAGE_DIRNAME, exist_ok = True)
    zstack_parameters = {'start': -120, 'end': 120, 'step': 30}
    image_filename_list = shoot_timelapse(mscope, image_dir = IMAGE_DIRNAME, zparams = zstack_parameters, total_snapshots = 1, period_sec = 1)

    # merge snapshots into a single video
    # date_sec = datetime.now().strftime("%Y%m%d_%H%M%S")
    # final_merged_video_name = 'miniscope_timelapse_merged_' + date_sec + '.mp4'
    # merge_snapshots(video_dirname, video_filename_list, ffmpeg_path, final_merged_video_name)

    # handle errors, if they happened
    if mscope.last_error:
        print('Error while acquiring data from Miniscope: {}'.format(mscope.last_error), file=sys.stderr)

    # disconnect from scope 
    mscope.disconnect()

    # cv2.destroyAllWindows()

    return

if __name__ == '__main__':
    main()
