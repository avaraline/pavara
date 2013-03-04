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

Windows: navigate to the source code directory with cmd and run ppython map_test.py

Macs: navigate to the source code directory in a terminal and run ppython map_test.py

Linux: navigate to the source code directory in a terminal and run python map_test.py

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
		*	fields
		*	walldoors
		*	goodies
		*	teleporters
		*	etc.

###low priority
*	**map loading**
	*	honor yaw/pitch/roll attributes for all objects, not just blocks
*   **map syntax**
	*   need definitions/implementation for
		*   per-level logic/scripting
		*	assign ids to objects for scripting
		*   fields/areas
		*   custom shapes
		*   assigning colors to shapes

Graphics
--------
###high priority
*   **walking animation**
    *   improvements
	*	work with colliision character to stop feet on terrain

###low priority
*   **updated assets**
	*   grenade model, finalize missle/plasma
	*   unigoody
*   **shadows**
    *   directional soft shadow mapping
*   **particle effects**
	*	explosions
	*	missle/lazer trails
	*	environmental, e.g. precipitation?

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
	*	shield/plasma recharge rates based on energy level
	*	ammo and boosters
	*	respawns
	*	incarnator selection
		*	random order, unless order attribute explicitly set on incarnator objects
		*	if multiple incarnators exist with same order value, select randomly within that subset
		*	do allow for team masking
		*	if number of players exceeds the number of incarnators, split players into "batches" and spawn them in ten second waves?
	*	position, speed, velocity
*	**game data**: setup, types, start/end conditions
*	**messages**: triggering and listening for simple events, both in XML and whatever scripting set up we use

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

Physics (Bullet)
-------
###higher priority
*	**kinematic character controller**
	*	improve collision detection
	*	send messages to hector object for animation
*	**ballistics**
	*	grenade lobbing
	*	"smart" missle tracking
	*	lazers
	*	damage

###lower priority
*	**other collidables**
	*	fields/areas
	*	kinematic map objects

User Interface
--------------
###lowest priority
*	**preliminary designs**
