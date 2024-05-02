CONDA_SCRIPT_PATH="/home/agroo/anaconda3/etc/profile.d/conda.sh"
TIMELAPSE_SCRIPT_PATH="/home/agroo/src/pomidaq-timelapse/timelapse/timelapse.py"

source $CONDA_SCRIPT_PATH
conda activate miniscope310

python $TIMELAPSE_SCRIPT_PATH "$@"

conda activate base