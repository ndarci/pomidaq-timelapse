# Miniscope Timelapse Control

`timelapse.py` is the main script for running the Miniscope in time lapse mode. In order to run the script, first follow the setup instructions in `../README.md`.

## Usage

```
python timelapse.py [film/merge] [-d output directory] [-e excitation strength] [-g gain] [-z z-stack parameters] [-t timesteps] [-p period]
```

## Options

### mode

Positional argument.

`film` records a series of time lapse images according to the given parameters, and merges them into a video at each working distance. 

`merge` takes a previously recorded set of images (must be provided using option `-d`) and merges them into a video at each working distance. This option is mainly useful for creating a video even if the time lapse fails partway through.

### directory

`-d` or `--directory`. Path to the output directory. Default global `BASE_IMAGE_DIRNAME`.

### excitation

`-e` or `--excitation`. Integer 0 - 100 representing LED excitation strength. Default 20.

### gain

`-g` or `--gain`. Integer 0 - 2 representing gain applied to captured images. Default 0.

### zstack

`-z` or `--zstack`. Three integers -120 - 120 representing working distance start, end, and step for each z-stack. Default [-120, 120, 10].

### timesteps

`-t` or `--timesteps`. Integer representing number of timesteps to capture for the time lapse. Default 10.

### period

`-p` or `--period`. Integer representing period in **seconds** between time lapse snapshots. Default 60. 


