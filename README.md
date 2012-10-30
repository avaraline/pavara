pavara
======

A game inspired by the classic Mac game.

* * *
how to install dependencies
===========================

Pavara depends on Panda3D which can be downloaded here: http://www.panda3d.org/download.php?sdk&version=1.8.0

For Windows: http://www.panda3d.org/download/panda3d-1.8.0/Panda3D-1.8.0.exe

For Macs: http://www.panda3d.org/download/panda3d-1.8.0/Panda3D-1.8.0.dmg

Mac users also need: https://developer.nvidia.com/cg-toolkit

For Ubuntu: http://www.panda3d.org/download.php?platform=ubuntu&version=1.8.0&sdk

For Ubuntu 12.04, you can install the oneiric version, but it will complain about 2 unmet dependencies. 

You can download those dependencies from here: http://packages.ubuntu.com/oneiric/allpackages. Then it will install.

running it
==========

Windows: navigate to the source code directory with cmd and run ppython pavara.py

Macs: navigate to the source code directory in a terminal and run ppython pavara.py

Linux: navigate to the source code directory in a terminal and run python pavara.py

* * *
roadmap
=======

Maps
----
###high priority
*   **legacy map converter**
	*   add conversion for
		*   domes
		*   rounded rects

###low priority
*   **map syntax**
	*   need definitions/implementation for
        *   level description
		*   per-level logic/scripting
		*	assign ids to objects for scripting
		*	assign mass to objects to make freeSolids
		*   fields/areas
		*   goodies
		*   custom shapes
		
Graphics
--------
###high priority
*   **walker animations**
	*   seperate animations for `walk, stand, crouched_walk, crouch, airbourne_walk`
	*   animation blending based on crouch/walk factor, physics forces, and terrain

###low priority
*   **updated assets**
    *   walker(s) (export bobski's model)
	*   missile/grenade/plasma
	*   unigoody
*   **shadows**
    *   directional soft shadow mapping
*   **particle effects**
	*	explosions
	*	missle/lazer trails
	
Networking
----------
###high priority
*   **game object distribution and sync**

###low priority
*   **server tracking**
*   **game metadata distribution (chat/level and asset distribution)**

Logic
-----
*	**player data**
	*	shield values, energy values, plasma cooldown
	*	ammo and boosters
	*	respawns
	*	incarnator selection
	*	position, speed, velocity
*	**game data**: setup, types, start/end conditions
	
Sound
-----
###low priority
*	**doppler effect/stereo positioned playback**
*	**updated assets**
	*	plasma/missle/grenade loop
	*	kArticWind etc. replacements
	*	footstep sounds, goody sounds
	*	incarnator and teleporter sounds
	*	xplosions

Physics (ODE)
-------
###higher priority
*	**kinematic character controller**
	*	apply forces after physics tick for movement
	*	keep collision shape upright
	*	send messages to hector object for animation
	*	update position and rotation of hector object
*	**ballistics**
	*	grenade lobbing
	*	"smart" missle tracking
	*	lazers
	*	damage 
	
###lower priority
*	**other collidables**
	*	goodies
	*	fields/areas
	*	kinematic map objects
    
User Interface
--------------
###lowest priority
*	**preliminary designs**
