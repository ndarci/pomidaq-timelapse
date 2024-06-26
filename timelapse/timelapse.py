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
import numpy as np

import logging
logger = logging.getLogger(__name__)

# tell python where compiled miniscope module is installed
sys.path.append('/lib/python3.10/dist-packages/')
from miniscope import Miniscope, ControlKind

from mscopeutil import stderr_redirected
from mscopesetup import setup_miniscope
from mscopecontrol import set_led, set_focus, set_gain, get_frame

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

    z_dir = z_int_to_string(z_index, focus)
    if not os.path.exists(os.path.join(image_dir, z_dir)):
        os.makedirs(os.path.join(image_dir, z_dir))

    # get all the relevant image info into the final filename
    img_name = 'miniscope_t' + str(time_step) + '_' + params_to_suffix(z_dir, led, gain) + '.jpg'
    
    return os.path.join(image_dir, z_dir, img_name)

# OG function, works perfectly until miniscope disconnects, sometimes produces blank frames
def take_photo0(m, nbuffer_frames = 50):
    '''Take a photo with the Miniscope'''
    nframes = 0
    while m.is_running and nframes < nbuffer_frames:
        frame = m.current_disp_frame
        if frame is not None:
            nframes += 1
    
    return frame

def take_photo(m):
    '''Take a photo with the Miniscope'''

    i = 0 # frame index
    frame = None
    buffer_frames = 50

    max_signal = 0
    max_frame = None

    # TODO: speed this up... almost never need all 50 frames. if signal is strong, take a frame then

    # sometimes the camera takes a few frames to warm up, give it a buffer to guarantee a good signal
    while i < buffer_frames:
        frame = get_frame(m)
        
        # if frame is not None:
        #     logger.debug('frame signal strength: ' + np.sum(frame))
        # else:
        #     logger.debug('frame is None')

        if frame is not None: # can't do math operations on None
            signal_strength = np.sum(frame)

            # save the frame with the strongest signal
            if signal_strength > max_signal:
                max_signal = signal_strength
                max_frame = frame

        i += 1

    return max_frame
        

def take_zstack(m, image_dir, time_step, zparams, led, gain, index_file):
    '''Shoot a z-stack of photos with the Miniscope'''
    current_focus = zparams['start']
    z_index = 0
    while current_focus <= zparams['end']:
        # update focus
        set_focus(m, current_focus)

        # remember metadata
        this_file_path = generate_file_path(image_dir, time_step, z_index, current_focus, led, gain)
        frame_start_time = get_date_sec()

        # try to take a photo
        frame = take_photo(m)

        if frame is None: # disconnected during z-stack
            logger.warning('Failed to take photo!')
            index_file.write(z_int_to_string(z_index, current_focus) + ',' + this_file_path + ',' + 'FAILED' + '\n')
            return False
        elif (not np.any(frame)): # got a blank photo
            logger.warning('Took a blank photo!')
            index_file.write(z_int_to_string(z_index, current_focus) + ',' + this_file_path + ',' + 'BLANK' + '\n')
            return False
        else: # success
            cv2.imwrite(this_file_path, frame) # write the image itself
            index_file.write(z_int_to_string(z_index, current_focus) + ',' + this_file_path + ',' + frame_start_time + '\n')

        current_focus += zparams['step']
        z_index += 1

    return True
        
def shoot_timelapse(image_dir, zparams, excitation_strength, gain, total_timesteps, period_sec, index_file):
    '''Shoot a timelapse, which will be a set of folders for each z-level, full of image files at each time point.'''

    logger.info("Starting time lapse recording.")
    logger.info("Total timesteps = " + str(total_timesteps))
    logger.info("Period (sec) = " + str(period_sec))
    logger.info("Z-Stack settings = " + str(zparams))

    timestep = 0
    attempts = 0
    max_attempts = 3 # number of times we allow a z-stack to fail before aborting

    # time lapse loop
    while timestep < total_timesteps:
        # connect to the miniscope and set proper control levels
        logger.info("Connecting to Miniscope")
        try:
            mscope = Miniscope() # create new Miniscope instance
            setup_miniscope(mscope, MINISCOPE_NAME, DAQ_ID) # run some diagnostics and start it running
            set_gain(mscope, gain)
            set_led(mscope, excitation_strength)

            # take a z-stack at the current state
            logger.info("Taking z-stack " + str(timestep))
            status = take_zstack(mscope, image_dir, timestep, zparams, excitation_strength, gain, index_file)
            attempts += 1

        finally:
            # turn off and disconnect from the miniscope
            set_led(mscope, 0)
            time.sleep(1)
            mscope.stop()
            mscope.disconnect()

        if status: # successful z-stack
            timestep += 1
            attempts = 0
            if timestep < total_timesteps:
                logger.info("Waiting " + str(period_sec) + " seconds to take next z-stack")
                time.sleep(period_sec)
        elif attempts >= max_attempts:
            logger.error('Z-stack failed on attempt ' + str(attempts) + ' (final attempt). Check the Miniscope connection.')
            break
        else:
            logger.warning('Z-stack failed on attempt ' + str(attempts) + '. Trying again.')            

    logger.info("Time lapse recording finished.")

def read_image_index(img_dir):
    '''read an index file of frame paths into a dictionary for merge function'''
    infile = open(os.path.join(img_dir, 'image_filename_index.csv'), 'r')
    img_fn_dict = {}
    for line in infile:
        splitline = line.strip().split(',')
        z_dir = splitline[0]
        img_path = splitline[1]
        if z_dir not in img_fn_dict.keys():
            img_fn_dict[z_dir] = [img_path]
        else:
            img_fn_dict[z_dir].append(img_path)
    # for each dict entry: key = z-level string, value = list of paths to all frames at that z-level
    return img_fn_dict

def merge_timelapse(ffmpeg_path, img_dir, img_fn_dict):
    '''Use ffmpeg to merge the miniscope images into a single video for each z-level'''

    # # slice up the filename of the first image file to extract the led and gain parameters
    # # fine to take the first bc these are constants for the whole timelapse
    # key0 = list(img_fn_dict.keys())[0]
    # filename0 = img_fn_dict[key0][0]
    # suffixlist = filename0.split('.')[0].split('_')[-3:]
    # suffix = '_'.join(suffixlist)

    for z_dir in img_fn_dict.keys():
        # remember parameters at this z-level for video filename
        suffixlist = [z_dir]
        # slice up first filename to get led and gain information
        filename0 = img_fn_dict[z_dir][0]
        suffixlist.extend(filename0.split('.')[0].split('_')[-2:])
        suffix = '_'.join(suffixlist)

        merged_video_name = 'miniscope_timelapse_' + suffix + '.mp4'
        merged_video_path = os.path.join(img_dir, z_dir, merged_video_name)
        subprocess.call([ffmpeg_path, \
                        '-framerate', '5', \
                        '-pattern_type', 'glob', \
                        '-i', img_dir + '/' + z_dir + '/*.jpg', \
                        '-hide_banner', '-loglevel', 'error', \
                        # '-s:v', '680x680', \
                        # '-c:v', 'libx264', \
                        # '-crf', '17', \
                        # '-pix_fmt', 'yuv420p', \
                        merged_video_path])
        
def setup_parser(p):
    '''Set up argument parser object and return parsed args'''

    help_m = '''Film mode shoots a series of time lapse videos at each z-level 
                and saves them in structured directories. Merge mode performs the second step only,
                merging a previously shot set of images into a video (default 'film').'''
    help_d = '''Base directory to write output images and merged videos.'''
    help_e = '''LED excitation strength (0 - 100).'''
    help_g = '''Gain applied to output images (0 - 2).'''
    help_z = '''Z-stack start, end, and step for each timepoint (-127 - +127).'''
    help_t = '''Number of time steps to record in the time lapse.'''
    help_p = '''Period between time lapse snapshots, in seconds.'''

    p.add_argument('mode', type = str, choices = ['film', 'merge'], default = 'film', help = help_m)
    p.add_argument('-d', '--directory', type = str, default = BASE_IMAGE_DIRNAME, help = help_d)
    p.add_argument('-e', '--excitation', type = int, default = 20, help = help_e)
    p.add_argument('-g', '--gain', type = int, default = 0, help = help_g)
    p.add_argument('-z', '--zstack', type = int, nargs = 3, default = [-120, 120, 10], help = help_z)
    p.add_argument('-t', '--timesteps', type = int, default = 10, help = help_t)
    p.add_argument('-p', '--period', type = int, default = 60, help = help_p)
    
def setup_logger(base_dir):
    '''Set up root logger config to write to stdout and a log file'''

    # add streams to stdout and log file
    stdoutHandler = logging.StreamHandler(stream=sys.stdout)
    logfileHandler = logging.FileHandler(os.path.join(base_dir, 'timelapse.log'))
    stdoutHandler.setLevel(logging.DEBUG)
    logfileHandler.setLevel(logging.DEBUG) # change to INFO eventually

    # set format
    fmt = logging.Formatter(
    "%(name)s: %(asctime)s | %(levelname)s | %(filename)s:%(lineno)s | %(process)d >>> %(message)s"
    )
    stdoutHandler.setFormatter(fmt)
    logfileHandler.setFormatter(fmt)

    logging.basicConfig(level = logging.DEBUG, handlers = [stdoutHandler, logfileHandler])

def get_date_sec():
    return datetime.now().strftime("%Y-%m-%d_%H%M%S")

def main():
    # set up argument parser and parse args
    parser = argparse.ArgumentParser()
    setup_parser(parser)
    args = parser.parse_args()

    # prep base image directory 
    date_sec = get_date_sec()
    image_dir_now = args.directory + '_' + str(date_sec)
    os.makedirs(image_dir_now)

    # set up logger
    setup_logger(image_dir_now)

    if args.mode == 'merge' and args.directory == BASE_IMAGE_DIRNAME:
        parser.error('merge mode requires a previously filmed image directory passed to -d.')

    if args.mode == 'film': # film mode
        try:
            # run timelapse and save all images
            index_file = open(os.path.join(image_dir_now, 'image_filename_index.csv'), 'w')
            shoot_timelapse(image_dir = image_dir_now, \
                            zparams = {'start': args.zstack[0], 'end': args.zstack[1], 'step': args.zstack[2]}, \
                            excitation_strength = args.excitation, \
                            gain = args.gain, \
                            total_timesteps = args.timesteps, \
                            period_sec = args.period, \
                            index_file = index_file)
                
        finally: # these resource-closing commands should run no matter what happens
            # close index file
            index_file.close()

        # tell the merge function where to find the image index file
        merge_dir = image_dir_now
    else:
        logger.info('Running in merge mode only. Filming parameters are ignored.')
        merge_dir = args.directory
    
    logger.info('Merging timelapse images in directory: ' + merge_dir)

    # merge images into a time lapse video
    merge_timelapse(FFMPEG_PATH, merge_dir, read_image_index(merge_dir))

    logger.info('Merge complete!')

    return

if __name__ == '__main__':
    # with stderr_redirected():
    #     main()
    main()
