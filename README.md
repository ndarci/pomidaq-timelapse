# Time lapse imaging with the Miniscope

TL;DR - The [PoMiDAQ](https://github.com/bothlab/pomidaq) software includes a Python module that can be used to control the Miniscope with a script, and has all the same features as the [UCLA Miniscope DAQ QT Software](https://github.com/Aharoni-Lab/Miniscope-DAQ-QT-Software). It's a bit tricky to set up because PoMiDAQ has to run on Linux for the Python module to work.

## Prerequisities

I set this up on a Windows laptop with the following specs:

| Hardware | |
---|---
Model | Dell Inspiron 3583
Device name | DESKTOP-H560LU9
Processor | Intel(R) Celeron(R) CPU 4205U @ 1.80GHz   1.80 GHz
Installed RAM | 20.0 GB (19.9 GB usable)
System type | 64-bit operating system, x64-based processor

| Software | |
---|---
Edition | Windows 10 Home
Version | 22H2
Installed on | 8/8/2021
OS build | 19045.4170
Experience | Windows Feature Experience Pack 1000.19054.1000.0

Our Miniscope is a __Miniscope v4.41 with the BNO sensor.__

If you are already on a Linux machine, skip to step 2. If you are on a Mac, you may need to dual-boot your machine with Linux for this to work.

## Step 1: Set up a Linux subsystem

### Base WSL

Before downloading PoMiDAQ, you need to have a Linux operating system running on your computer. You can do this either with WSL or by dual-booting (I used WSL).

WSL will run a Linux operating system inside your Windows machine, installing the new filesystem at ```/```, your computer's "root." You can access your Linux files from Windows and vice versa.

To set up WSL, follow the instructions here: https://learn.microsoft.com/en-us/windows/wsl/install

* I installed Ubuntu 22.04.3 LTS
* Verify that you are running WSL2. There are instructions in the above link on how to check, and upgrade if WSL1 if needed.

Once everything is installed, make sure the installation has worked by opening Powershell as administrator and typing ```wsl``` or ```bash```. You should see a new command prompt appear that ends in ```$```. From now on, use either of these commands to launch WSL from Powershell.

### Custom video-linked WSL

After installing the default WSL, you will need to re-compile the WSL kernel so that PoMiDAQ can recognize video devices plugged into your Windows machine via USB (i.e. the Miniscope). 

To do this, __carefully__ follow the instructions here: https://github.com/PINTO0309/wsl2_linux_kernel_usbcam_enable_conf?tab=readme-ov-file

Once this process finishes, you will need to "attach" the Miniscope USB device to WSL using a tool called USBIPD-WIN. To do this, follow the instructions here: https://learn.microsoft.com/en-us/windows/wsl/connect-usb

Remember that Windows will not recognize the Miniscope over USB while it is linked to WSL. If you ever want to go back to using the Miniscope with the UCLA Software, just follow the step at the end of the above tutorial to "detach" the device from WSL.


## Step 2: Gather the tools you need to run PoMiDAQ

### Anaconda

The Anaconda distribution will allow you to manage Python versions and packages using virtual environments. 

To install it, follow the instructions here, choosing the __command-line installer for Linux__ and accepting the default for all the options: https://docs.anaconda.com/free/anaconda/install/linux/

When the installer finishes running, verify that it worked by opening WSL and typing:

```
conda activate
```

This should activate your ```base``` environment, and put ```(base)``` at the beginning of your command prompt.

Leave Anaconda here for now, and we'll use it to create a virtual environment with all the necessary packages once PoMiDAQ is installed.

### Visual Studio Code

Install VS Code for __Windows, not Linux__, using the link here: https://code.visualstudio.com/

Once the installer finishes running, you can open VS Code by opening a WSL prompt and typing ```code```. When VS Code opens and asks if you want to install the WSL extension, say yes. 

### git

[git](https://git-scm.com/) will allow you to have version control in your projects and clone repositories. Install it in WSL using:

```
apt-get install git
```

### cmake

cmake will allow you to compile the miniscope Python module. If ```which cmake``` in WSL gives you nothing back, install the Linux x86 binary in WSL (updating the version if needed) using: 

```
cd /home/<your_username>/src/
wget https://github.com/Kitware/CMake/releases/download/v3.29.2/cmake-3.29.2-linux-x86_64.sh
./cmake-3.29.2-linux-x86_64.sh
```

## Step 3: Set up the PoMiDAQ GUI

Download the latest Linux/Ubuntu PoMiDAQ binary from their release site: https://github.com/bothlab/pomidaq/releases

Install the ```.deb``` file by opening WSL, ```cd```'ing to the folder where it downloaded, and running the following (replacing the PoMiDAQ version with the one you downloaded if needed):

```
sudo dpkg -i pomidaq_0.5.1+git300.ubuntu22.04_amd64.deb
```

If there are any dependencies it needs to install or update, accept all of them.

When the installer finishes, verify that it worked by opening WSL and typing ```pomidaq```. A GUI window should pop up with the Miniscope controls, and you should see a live feed after pressing the Connect button.

## Step 4: Compile the PoMiDAQ Python module

Now that you have a working PoMiDAQ GUI, the final step is to set up the Python module so that you can control the Miniscope with a custom script.

From this point on, it will be a good idea to run everything inside VS Code. Open a new WSL terminal and type ```code```.

### Creating a project directory

When VS Code opens, open a new WSL Terminal by clicking __View > Terminal__. 

You should be in your Linux ```home``` folder, ```/home/<your_username>/```. Start by creating a directory for this and other future coding projects, then enter that directory:

```
mkdir src
cd src
```

Now, clone my custom fork of the PoMiDAQ GitHub:

```
git clone https://github.com/ndarci/pomidaq-timelapse.git
```

Enter the project directory with:

```
cd pomidaq-timelapse
```

It will also be very useful to open this project directory in the VS Code file explorer. To do this, click __File > Open Folder...__ and navigate to ```/home/<your_username>/src/pomidaq-timelapse/```.

### Creating a custom conda environment

If you don't already see ```(base)``` before your command prompt, type

```
conda activate
```

Create a new conda environment called ```miniscope310``` with Python version 3.10:

```
conda create --name miniscope310 python=3.10
```

Activate the environment (you should see ```(miniscope310)``` before your command prompt), then install the packages we'll need to compile the PoMiDAQ Python module:

```
conda activate miniscope310
pip install opencv-python
pip install pybind11
conda install numpy
```

### Compiling the miniscope Python module

Using the VS Code file explorer in the left sidebar, double-click the file ```py/CMakeLists.txt```.

Modify the three lines at the beginning to match your username and PoMiDAQ/Anaconda installation locations.

Create a build directory inside the ```py``` folder, and enter that directory:

```
mkdir py/build
cd py/build
```

Use cmake to compile the miniscope Python module:

```
cmake ../
```

If the build succeeds, you should be able to see the compiled library file stored at ```/lib/python3.10/dist-packages/miniscope.cpython-310-x86_64-linux-gnu.so```. 

You should now be able to run the ```py/example.py``` Python script to control the Miniscope!

There is unfortunately no API documentation for all the functions available in the miniscope module, but the example script should demonstrate enough to get started.

For an example of a time lapse script, see ```timelapse/timelapse.py```. Note that you will need to install the [ffmpeg](https://ffmpeg.org/) software to merge the snapshot videos together.


