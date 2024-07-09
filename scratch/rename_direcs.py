import os

basedir = '/home/agroo/niko_miniscope_vids/'
lsraw = os.listdir(basedir)
renameme = [d for d in lsraw if (d[0] != '2') and ('2' in d)]

for oldname in renameme:
    splitname = oldname.split('_')
    datestr = '_'.join(splitname[-2:])
    labelstr = '_'.join(splitname[:-2])
    newname = '_'.join([datestr, labelstr])
    os.rename(os.path.join(basedir, oldname), os.path.join(basedir, newname))
