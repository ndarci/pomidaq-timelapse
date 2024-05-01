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
import argparse

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

    # TODO: get a precise timestamp of when the image was taken, store in name or metadata... or a log file I save in parent direc? even a csv I could analyze?

    z_dir = z_int_to_string(z_index, focus)
    if not os.path.exists(os.path.join(image_dir, z_dir)):
        os.makedirs(os.path.join(image_dir, z_dir))

    # get all the relevant image info into the final filename
    img_name = 'miniscope_t' + str(time_step) + '_' + params_to_suffix(z_dir, led, gain) + '.jpg'
    
    return os.path.join(image_dir, z_dir, img_name)

def take_photo(m, nbuffer_frames = 50):
    '''Take a photo with the Miniscope'''

    # TODO: somehow control for the frames that are all covered in horizontal lines?
    # TODO: get rid of little BNO indicator logo in bottom corner
    # TODO: write some try - except handling for the bug where we get 'failed to grab frame' mid time lapse... maybe reconnect?

    # it takes a few frames to warm up, throw away the first (nbuffer_frames - 1) frames, then save the last
    nframes = 0
    frame = None
    while m.is_running and nframes < nbuffer_frames:
        time.sleep(0.01)
        frame = m.current_disp_frame
        nframes += 1
        
    # temp code to reproduce frame grabbing issue
    now = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    if int(now[-1]) == 3:
        frame = None
        m.disconnect()

    # if it fails to grab a frame, disconnect and reconnect to scope
    if frame is None:
        print()
        print('Miniscope disconnected. Reconnecting...')
        time.sleep(2)
        m.disconnect()
        setup_miniscope(m, MINISCOPE_NAME, DAQ_ID)
        time.sleep(2)
        frame = take_photo(m)

    # fix this... returns a black frame when it disconnects

    return frame
        

def take_zstack(m, image_dir, time_step, zparams, led, gain, filenames):
    '''Shoot a z-stack of photos with the Miniscope'''
    current_focus = zparams['start']
    z_index = 0
    while current_focus <= zparams['end']:
        this_file_path = generate_file_path(image_dir, time_step, z_index, current_focus, led, gain)

        set_focus(m, current_focus)
        frame = take_photo(m)
        if frame is not None:
            cv2.imwrite(this_file_path, frame)
        else:
            print('Failed to take photo!')

        filenames[z_int_to_string(z_index, current_focus)].append(this_file_path)
        current_focus += zparams['step']
        z_index += 1
        
    return filenames

def write_image_index(img_dir, img_fn_dict):
    outfile = open(os.path.join(img_dir, 'image_filename_index.csv'), 'w')
    for z_dir, img_paths in img_fn_dict.items():
        outfile.write(z_dir + ',' + ','.join(img_paths) + '\n')
    outfile.close()

def read_image_index(img_dir):
    infile = open(os.path.join(img_dir, 'image_filename_index.csv'), 'r')
    img_fn_dict = {}
    for line in infile:
        splitline = line.strip().split(',')
        z_dir = splitline[0]
        img_paths = splitline[1:]
        img_fn_dict[z_dir] = img_paths
    return img_fn_dict


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
    i = 0
    for z in range(zparams['start'], zparams['end']+1, zparams['step']):
        filenames[z_int_to_string(i, z)] = []
        i += 1

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

def merge_timelapse(ffmpeg_path, img_dir, img_fn_dict):
    '''Use ffmpeg to merge the miniscope images into a single video for each z-level'''

    # slice up the filename of the first image file to extract the led and gain parameters
    # fine to take the first bc these are constants for the whole timelapse
    key0 = list(img_fn_dict.keys())[0]
    filename0 = img_fn_dict[key0][0]
    suffixlist = filename0.split('.')[0].split('_')[-3:]
    suffix = '_'.join(suffixlist)

    for z_dir in img_fn_dict.keys():
        merged_video_name = 'miniscope_timelapse_' + suffix + '.mp4'
        merged_video_path = os.path.join(img_dir, z_dir, merged_video_name)
        subprocess.call([ffmpeg_path, \
                        '-framerate', '5', \
                        '-pattern_type', 'glob', \
                        '-i', img_dir + '/' + z_dir + '/*.jpg', \
                        # '-s:v', '680x680', \
                        # '-c:v', 'libx264', \
                        # '-crf', '17', \
                        # '-pix_fmt', 'yuv420p', \
                        merged_video_path])

def main():
    parser = argparse.ArgumentParser()

    help_m = '''Film mode shoots a series of time lapse videos at each z-level 
                and saves them in structured directories. Merge mode performs the second step only,
                merging a previously shot set of images into a video (default 'film').'''
    help_d = '''Base directory to write output images and merged videos.'''
    help_e = '''LED excitation strength (0 - 100).'''
    help_g = '''Gain applied to output images (0 - 2).'''
    help_z = '''Z-stack start, end, and step for each timepoint (-127 - +127).'''
    help_t = '''Number of time steps to record in the time lapse.'''
    help_p = '''Period between time lapse snapshots, in seconds.'''

    parser.add_argument('mode', type = str, choices = ['film', 'merge'], default = 'film', help = help_m)
    parser.add_argument('-d', '--directory', type = str, default = BASE_IMAGE_DIRNAME, help = help_d)
    parser.add_argument('-e', '--excitation', type = int, default = 20, help = help_e)
    parser.add_argument('-g', '--gain', type = int, default = 0, help = help_g)
    parser.add_argument('-z', '--zstack', type = int, nargs = 3, default = [-120, 120, 10], help = help_z)
    parser.add_argument('-t', '--timesteps', type = int, default = 10, help = help_t)
    parser.add_argument('-p', '--period', type = int, default = 60, help = help_p)
    
    args = parser.parse_args()

    if args.mode == 'merge' and args.directory == BASE_IMAGE_DIRNAME:
        parser.error('merge mode requires a previously filmed image directory passed to -d.')

    if args.mode == 'film': # film mode
        # create new Miniscope instance
        mscope = Miniscope()

        # run some diagnostics and start it running
        setup_miniscope(mscope, MINISCOPE_NAME, DAQ_ID)

        # prep image directory and initial parameters
        date_sec = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        image_dir_now = args.directory + '_' + str(date_sec)
        os.makedirs(image_dir_now)
        set_gain(mscope, args.gain) # gain is constant
        zstack_parameters = {'start': args.zstack[0], 'end': args.zstack[1], 'step': args.zstack[2]}

        # run timelapse and save all images
        image_filename_dict = shoot_timelapse(mscope, \
                                                image_dir = image_dir_now, \
                                                zparams = zstack_parameters, \
                                                excitation_strength = args.excitation, \
                                                gain = args.gain, \
                                                total_timesteps = args.timesteps, \
                                                period_sec = args.period)

        # write image filenames to an index file for merge function
        write_image_index(image_dir_now, image_filename_dict)

        # print(image_filename_dict)
        # print()
        # print(read_image_index(image_dir_now))

        # disconnect from scope 
        mscope.disconnect()

        # tell the merge function where to find the image index file
        merge_dir = image_dir_now
    else:
        print()
        print('Running in merge mode only. Filming parameters are ignored.')
        merge_dir = args.directory
    
    print()
    print('Merging timelapse images in directory: ' + merge_dir + ' ... ')
    print()

    # merge images into a time lapse video
    merge_timelapse(FFMPEG_PATH, merge_dir, read_image_index(merge_dir))

    print()
    print('Merge complete!')

    return

if __name__ == '__main__':
    main()
