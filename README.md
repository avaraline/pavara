
<img src="https://dl.dropboxusercontent.com/u/38430353/walker-sunset.png" width="720"/>
* * *
how to install dependencies
---------------------------

The game depends on [Panda3d](http://www.panda3d.org/download.php?sdk&version=1.8.0). Panda3d installs its own version of python, but to run the map converter and other helper tools in the repo you will need python >= 2.7 installed on your system.

Panda3d installer links: [Windows](http://www.panda3d.org/download/panda3d-1.8.0/Panda3D-1.8.0.exe), [Mac](http://www.panda3d.org/download/panda3d-1.8.0/Panda3D-1.8.0.dmg), [Linux (Ubuntu)](http://www.panda3d.org/download.php?platform=ubuntu&version=1.8.0&sdk).

Mac users also need the [NVidia CG toolkit](https://developer.nvidia.com/cg-toolkit). Mac users may also need an [X11 Server](http://xquartz.macosforge.org/trac) if one is not installed.

In Ubuntu 12.04, the `oneiric` version of Panda3d will complain about 2 unmet dependencies during installation. Download and install the missing packages [from here](http://packages.ubuntu.com/oneiric/allpackages) and retry installation.

running
-------
The python script `map_test.py` must be run with the `ppython` command (provided by Panda3d) inside the source directory.

* Windows: open a new `cmd.exe`, `dir \Wherever\You\Saved\the_game` then `ppython map_test.py`

* Mac/Linux: open a new terminal and `cd /path/to/game/folder` followed by `ppython map_test.py`

