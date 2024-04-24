#!/usr/bin/env python3

# script to run the miniscope in time-lapse mode, adapted from ../py/example.py

# define key strings for setup and recording
MINISCOPE_NAME = 'Miniscope_V4_BNO'  # the device type we want to connect to
DAQ_ID = 0  # the video device ID of our DAQ box
BASE_IMAGE_DIRNAME = '/home/agroo/niko_miniscope_vids/timelapse_test' # path to the folder we will store time lapse images in
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

def z_int_to_string(z_index, focus):
    '''Convert a z-level integer and its index to a friendlier string for filepaths'''
    # get rid of dashes in negatives
    if focus < 0:
        focus_str = 'neg' + str(abs(focus))
    else:
        focus_str = str(focus)
    z_str = 'z' + str(z_index) + '-' + focus_str
    return z_str

def params_to_suffix(z_str, led, gain):
    return z_str + '_led' + str(led) + '_gain' + str(gain)

def generate_file_path(image_dir, time_step, z_index, focus, led, gain):
    '''Generate an absolute path for a single image, using all the info associated with that image. Create the z directory if needed.'''

    # TODO: get a precise timestamp of when the image was taken, store in name or metadata

    z_dir = z_int_to_string(z_index, focus)
    if not os.path.exists(os.path.join(image_dir, z_dir)):
        os.makedirs(os.path.join(image_dir, z_dir))

    # get all the relevant image info into the final filename
    img_name = 'miniscope_t' + str(time_step) + '_' + params_to_suffix(z_dir, led, gain) + '.jpg'
    
    return os.path.join(image_dir, z_dir, img_name)

def take_photo(m, image_fn, nbuffer_frames = 50):
    '''Take a photo with the Miniscope'''

    # TODO: somehow control for the frames that are all covered in horizontal lines?
    # TODO: get rid of little BNO indicator logo in bottom corner

    # it takes a few frames to warm up, throw away the first (nbuffer_frames - 1) frames, then save the last
    nframes = 0
    while m.is_running and nframes < nbuffer_frames:
        frame = m.current_disp_frame
        if frame is not None:
            nframes += 1
    cv2.imwrite(image_fn, frame)

def take_zstack(m, image_dir, time_step, zparams, led, gain, filenames):
    '''Shoot a z-stack of photos with the Miniscope'''
    current_focus = zparams['start']
    z_index = 0
    while current_focus <= zparams['end']:
        this_file_path = generate_file_path(image_dir, time_step, z_index, current_focus, led, gain)

        set_focus(m, current_focus)
        take_photo(m, this_file_path)

        filenames[current_focus].append(this_file_path)
        current_focus += zparams['step']
        z_index += 1
        
    return filenames

def print_hline():
    print('--------------------')

def shoot_timelapse(m, image_dir, zparams, excitation_strength, gain, total_timesteps, period_sec):
    '''Shoot a timelapse, which will be a set of folders for each z-level, full of image files at each time point.'''

    print()
    print_hline()
    print("Starting time lapse recording.")
    print("\tTotal timesteps = " + str(total_timesteps))
    print("\tPeriod (sec) = " + str(period_sec))
    print("\tZ-Stack settings = " + str(zparams))
    print_hline()

    timestep = 0
    filenames = {}
    for z in range(zparams['start'], zparams['end']+1, zparams['step']):
        filenames[z] = []

    # time lapse loop
    while timestep < total_timesteps:
        print()
        print("Taking z-stack " + str(timestep) + " ...")
        
        # turn the LED on
        set_led(m, excitation_strength)

        # take a z-stack at the current state
        filenames = take_zstack(m, image_dir, timestep, zparams, excitation_strength, gain, filenames)
        
        # turn the LED off
        set_led(m, 0)
        
        timestep += 1

        if timestep < total_timesteps:
            print()
            print("Waiting", period_sec, "seconds to take next z-stack ...")
            time.sleep(period_sec)

    # stop recording and running miniscope
    m.stop()

    print()
    print_hline() 
    print("Time lapse recording finished.")
    print_hline()
    print()

    return filenames

def merge_timelapse(ffmpeg_path, img_dir, img_fn_dict, led, gain):
    '''Use ffmpeg to merge the miniscope images into a single video for each z-level'''
    for z in img_fn_dict.keys():
        z_dir = z_int_to_string(z)
        merged_video_name = 'miniscope_timelapse_' + params_to_suffix(z_dir, led, gain) + '.mp4'
        subprocess.call([ffmpeg_path, \
                        '-framerate', '30', \
                        '-pattern_type', 'glob', \
                        '-i', img_dir + '/' + z_dir + '/*.jpg', \
                        '-s:v', '680x680', \
                        '-c:v', 'libx264', \
                        '-crf', '17', \
                        '-pix_fmt', 'yuv420p', \
                        merged_video_name])

def main():
    # create new Miniscope instance
    mscope = Miniscope()

    # run some diagnostics and start it running
    setup_miniscope(mscope, MINISCOPE_NAME, DAQ_ID)

    # set initial control levels
    set_led(mscope, 0)
    set_focus(mscope, 0)
    set_gain(mscope, 0)

    # run timelapse loop and save all images
    date_sec = datetime.now().strftime("%Y%m%d_%H%M%S")
    image_dir_now = BASE_IMAGE_DIRNAME + '_' + str(date_sec)
    os.makedirs(image_dir_now, exist_ok = True)
    zstack_parameters = {'start': -120, 'end': 120, 'step': 240}
    excitation_strength = 20
    gain = 0
    image_filename_dict = shoot_timelapse(mscope, \
                                            image_dir = image_dir_now, \
                                            zparams = zstack_parameters, \
                                            excitation_strength = excitation_strength, \
                                            gain = gain, \
                                            total_timesteps = 2, \
                                            period_sec = 1)

    # print(image_filename_dict)

    # merge images into a time lapse video
    merge_timelapse(FFMPEG_PATH, image_dir_now, image_filename_dict, excitation_strength, gain)

    # disconnect from scope 
    mscope.disconnect()

    # cv2.destroyAllWindows()

    return

if __name__ == '__main__':
    main()
