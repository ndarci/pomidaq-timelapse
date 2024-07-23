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

def generate_file_path(image_dir, time_step, z_index, focus, led, gain, img_format, zselect = False):
    '''Generate an absolute path for a single image, using all the info associated with that image. Create the z directory if needed.'''

    z_dir = z_int_to_string(z_index, focus)
    if not os.path.exists(os.path.join(image_dir, z_dir)):
        os.makedirs(os.path.join(image_dir, z_dir))

    # get all the relevant image info into the final filename
    img_name = 'miniscope_t' + str(time_step) + '_' + params_to_suffix(z_dir, led, gain) + '.' + img_format
    
    if zselect:
        # generate a modified path for image copies going into the zselect folder 
        finalpath = os.path.join(image_dir, 'zselect', img_name)
    else:
        finalpath = os.path.join(image_dir, z_dir, img_name)

    return finalpath

# # orig version of take_photo, hangs if miniscope disconnects, sometimes sends out blank frames
# def take_photo0(m, nbuffer_frames = 50):
#     '''Take a photo with the Miniscope'''
#     nframes = 0
#     while m.is_running and nframes < nbuffer_frames:
#         frame = m.current_disp_frame
#         if frame is not None:
#             nframes += 1
    
#     return frame

# # less efficient version of take_photo, grabs way more frames than needed for most cases
# def take_photo1(m):
#     '''Take a photo with the Miniscope'''
#     i = 0
#     frame = None
#     buffer_frames = 50
#     while i<buffer_frames:
#         frame = get_frame(m)
#         i += 1
#     return frame    

def frame_debug_info(f):
    if f is None:
        logger.debug('Frame is None')
    else:
        fmax = np.max(f)
        fsum = np.sum(f)
        logger.debug('Frame max: ' + str(fmax))
        logger.debug('Frame sum: ' + str(fsum))

def warm_up_miniscope(m):
    '''Flushes through a bunch of frames to get the signal started on a freshly connected Miniscope.'''
    i = 0
    flush_size = 100
    signal_threshold = 10

    while i < flush_size:
        frame = get_frame(m)
        # frame_debug_info(frame)
        i += 1
    
    return np.max(frame) > signal_threshold

def take_photo(m):
    '''Take a photo with the Miniscope'''

    i = 0 # frame index
    frame = None
    timeout_frame_min = 100 # stop trying after this many blank/none frames

    good_frame_count = 0
    good_frame_min = 3 # take this many frames after we start getting signal

    # when it first connects, the camera sends zero signal for a few dozen frames
    # wait until a signal is detected for a few frames at a time, then save the newest one
    while i < timeout_frame_min:
        frame = get_frame(m)
        # frame_debug_info(frame)
        
        if frame is not None:
            if np.any(frame):
                good_frame_count += 1

            if good_frame_count >= good_frame_min:
                break

        i += 1

    return frame
        

def take_zstack(m, image_dir, time_step, zparams, led, gain, index_file, img_format):
    '''Shoot a z-stack of photos with the Miniscope'''
    current_focus = zparams['start']
    z_index = 0

    logger.info('Warming up Miniscope')
    if not warm_up_miniscope(m): # failed to start grabbing frames with signal
        logger.warning('Failed to detect frames with signal. You may want to check the sample and excitation.')
        return False
    
    while current_focus <= zparams['end']:
        # update focus
        set_focus(m, current_focus)

        # remember metadata
        this_file_path = generate_file_path(image_dir, time_step, z_index, current_focus, led, gain, img_format)
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
            
            # on first timestep, add image to z-level selecting folder
            if time_step == 0:
                if not os.path.exists(os.path.join(image_dir, 'zselect')):
                    os.makedirs(os.path.join(image_dir, 'zselect'))
                cv2.imwrite(generate_file_path(image_dir, time_step, z_index, current_focus, led, gain, img_format, zselect = True), frame)


        current_focus += zparams['step']
        z_index += 1

    return True
        
def shoot_timelapse(image_dir, zparams, excitation_strength, gain, total_timesteps, period_sec, index_file, img_format):
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
            status = take_zstack(mscope, image_dir, timestep, zparams, excitation_strength, gain, index_file, img_format)
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

def merge_timelapse(ffmpeg_path, img_dir, img_fn_dict, img_format):
    '''Use ffmpeg to merge the miniscope images into a single video for each z-level'''

    for z_dir in img_fn_dict.keys():
        # remember parameters at this z-level for video filename
        suffixlist = [z_dir]
        # slice up first filename to get led and gain information
        filename0 = img_fn_dict[z_dir][0]
        suffixlist.extend(os.path.basename(filename0).split('.')[0].split('_')[-2:])
        suffix = '_'.join(suffixlist)

        merged_video_name = 'miniscope_timelapse_' + suffix + '.mp4'
        merged_video_path = os.path.join(img_dir, z_dir, merged_video_name)
        subprocess.call([ffmpeg_path, \
                        '-framerate', '5', \
                        '-pattern_type', 'glob', \
                        '-i', img_dir + '/' + z_dir + '/*.' + img_format, \
                        '-hide_banner', '-loglevel', 'error', \
                        # '-s:v', '680x680', \
                        # '-c:v', 'libx264', \
                        # '-crf', '17', \
                        '-pix_fmt', 'yuv420p', \
                        merged_video_path])
        
def setup_parser(p):
    '''Set up argument parser object and return parsed args'''

    help_d = '''Base directory to write output images and merged videos. A unique date string 
                will be added to the beginning of the final directory name.'''
    help_e = '''LED excitation strength.'''
    help_g = '''Gain applied to output images.'''
    help_z = '''Z-stack start, end, and step for each timepoint.'''
    help_t = '''Number of time steps to record in the time lapse.'''
    help_p = '''Period between time lapse snapshots, in seconds.'''
    help_f = '''Format to save time lapse images in.'''
    help_m = '''Merge mode does not film a new time lapse, but merges a previously shot 
                set of images into videos at each z-level. You must provide a directory 
                with a previous time lapse stored in it.'''

    p.add_argument('-d', '--directory', type = str, default = BASE_IMAGE_DIRNAME, help = help_d)
    p.add_argument('-e', '--excitation', type = int, choices = range(0, 101), metavar = '[0-100]', default = 20, help = help_e)
    p.add_argument('-g', '--gain', type = int, choices = range(0, 3), metavar = '[0-2]', default = 0, help = help_g)
    p.add_argument('-z', '--zstack', type = int, choices = range(-120, 121), metavar = '[-120 - 120]', nargs = 3, default = [-120, 120, 10], help = help_z)
    p.add_argument('-t', '--timesteps', type = int, default = 24, help = help_t)
    p.add_argument('-p', '--period', type = int, default = 3600, help = help_p)
    p.add_argument('-f', '--imgformat', type = str, choices = ['png', 'jpg', 'tiff'], default = 'png', help = help_f)
    p.add_argument('-m', '--merge', action = 'store_true', default = False, help = help_m)

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
    if args.directory[-1] == '/':
        args.directory = args.directory[:-1]
    date_sec = get_date_sec()
    head, tail = os.path.split(args.directory)
    image_dir_now = head + '/' + str(date_sec) + '_' + tail
    os.makedirs(image_dir_now)

    # set up logger
    setup_logger(image_dir_now)

    if args.merge == True and args.directory == BASE_IMAGE_DIRNAME:
    # if args.mode == 'merge' and args.directory == BASE_IMAGE_DIRNAME:
        parser.error('merge mode requires a previously filmed image directory passed to -d.')

    if args.merge == False: # film mode
    # if args.mode == 'film': # film mode
        try:
            # run timelapse and save all images
            index_file = open(os.path.join(image_dir_now, 'image_filename_index.csv'), 'w')
            shoot_timelapse(image_dir = image_dir_now, \
                            zparams = {'start': args.zstack[0], 'end': args.zstack[1], 'step': args.zstack[2]}, \
                            excitation_strength = args.excitation, \
                            gain = args.gain, \
                            total_timesteps = args.timesteps, \
                            period_sec = args.period, \
                            index_file = index_file,
                            img_format = args.imgformat)
                
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
    merge_timelapse(FFMPEG_PATH, merge_dir, read_image_index(merge_dir), args.imgformat)

    logger.info('Merge complete!')

    return

if __name__ == '__main__':
    main()
