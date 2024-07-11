# Miniscope Timelapse Control

`timelapse.py` is the main script for running the Miniscope in time lapse mode. In order to run the script, first follow the setup instructions in `../README.md`.

For instructions on getting the program set up in the Groover Lab, see [below](##groover-lab-setup). 

## Usage

```
python timelapse.py [film/merge] [-d output directory] [-e excitation strength] [-g gain] [-z z-stack parameters] [-t timesteps] [-p period]
```

## Options

### mode

Positional argument.

`film` records a series of time lapse images according to the given parameters, and merges them into a video at each working distance. 

`merge` takes a previously recorded set of images (must be provided using option `-d`) and merges them into a video at each working distance. This option is mainly useful for creating a video after the time lapse fails partway through.

### directory

`-d` or `--directory`. Path to the output directory. A unique date string will be added to the beginning of the final directory name. Default global `BASE_IMAGE_DIRNAME`.

### excitation

`-e` or `--excitation`. Integer [0, 100] representing LED excitation strength. Default 20.

### gain

`-g` or `--gain`. Integer [0, 2] representing gain applied to captured images. Default 0.

### zstack

`-z` or `--zstack`. Three integers, separated by spaces, representing working distance start [-120, 120], end [-120, 120], and step [1, (end-start)] for each z-stack. Default `-120 120 10`.

### timesteps

`-t` or `--timesteps`. Positive integer representing number of timesteps to capture for the time lapse. Default 10.

### period

`-p` or `--period`. Positive integer representing period in **seconds** between time lapse snapshots. Default 60. 


## Groover Lab Setup

Start with the laptop turned off and the Miniscope unplugged from the USB port.



