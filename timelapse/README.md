# Miniscope Timelapse Control

`timelapse.py` is the main script for running the Miniscope in time lapse mode. In order to run the script, first follow the setup instructions in `../README.md`.

For instructions on getting the program set up in the Groover Lab, see [below](#groover-lab-setup). 

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

The time lapse program runs on a virtual Linux system (WSL) inside the laptop's Windows operating system. Before running it, you need to use the terminal to allow WSL to communicate with the Miniscope via the laptop's USB ports.

Start like this:
* Laptop and DAQ box plugged into power
* Laptop logged out or turned off
* DAQ box unplugged from laptop USB port 
* Miniscope plugged into DAQ box at "Scope" port

Log into the laptop with the password in the `USFS ORISE - Niko/miniscope` Drive folder.

Open Windows PowerShell. When you see the PowerShell command prompt, `PS C:\Users\agroo>`, run the following command to activate the Linux subsystem:

```
wsl
```

After a moment you will see the WSL command prompt, `(base) agroo@DESKTOP-H560LU9:/mnt/c/Users/agroo$`. Leave this WSL window open, and right-click on the PowerShell logo in the dock. In the menu that pops up, click `Windows PowerShell` to open a new terminal.

Now you will have two terminal windows open - one running PowerShell and one running WSL. Use the command prompts from above to tell them apart.  

Now, plug the DAQ box into one of the laptop's USB ports. Inside the PowerShell terminal, run the following command to list connected USB devices:

```
usbipd list
```

You should see an output like this:

```
Connected:
BUSID  VID:PID    DEVICE                                                        STATE
1-6    0c45:671e  Integrated Webcam                                             Not shared
1-10   0cf3:e009  Qualcomm QCA9377 Bluetooth                                    Not shared
1-13   04b4:00f9  MINISCOPE                                                     Shared

Persisted:
GUID                                  DEVICE
8e0ebd17-1ea7-4020-9473-ea7056040b0c  MINISCOPE
```

Notice the `MINISCOPE` device on the third row of the table. Depending on which USB port you plugged it into, its BUSID will either be `1-13` or `1-14`. To allow WSL to communicate with the Miniscope, run the following command, adjusting the `--busid` parameter according to the output you saw above if needed:

```
usbipd attach --wsl --busid 1-13
```

Now, switch over to the WSL terminal window. To verify that the USB linking worked, run the following:

```
lsusb
```

You should see an output like this, including `MINISCOPE`:

```
Bus 002 Device 002: ID 04b4:00f9 Cypress Semiconductor Corp. MINISCOPE
Bus 002 Device 001: ID 1d6b:0003 Linux Foundation 3.0 root hub
Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
```

If this looks good, navigate to the time lapse folder:

```
cd ~/src/pomidaq-timelapse/timelapse
```

Next, activate the Python environment with all the right libraries to run the time lapse program:

```
conda activate miniscope310
```

Your command prompt should now start with `(miniscope310)`. 

From here, you can open the PoMiDAQ graphical interface to get the sample in focus:

```
pomidaq
```

After running this command, the PoMiDAQ app should launch. Click `Connect`, and when a signal appears, use the excitation (LED), gain, and EWL (focus) controls to get a good view of your sample. When you're happy with your signal, place a box on top of the whole setup to block the room lights. Remember the excitation and gain levels you used, and take care not to move the Miniscope at all. Turn the excitation back to 0 to avoid photobleaching your sample. Close the PoMiDAQ app and go back to the WSL terminal.

From here, you can follow the [Usage](#usage) instructions above to record a time lapse!

