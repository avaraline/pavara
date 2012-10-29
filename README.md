pavara
======

A game inspired by the classic Mac game.

how to install dependencies
===========================

Pavara depends on Panda3D which can be downloaded here: http://www.panda3d.org/download.php?sdk&version=1.8.0

For Windows: http://www.panda3d.org/download/panda3d-1.8.0/Panda3D-1.8.0.exe

For Macs: http://www.panda3d.org/download/panda3d-1.8.0/Panda3D-1.8.0.dmg

For Ubuntu: http://www.panda3d.org/download.php?platform=ubuntu&version=1.8.0&sdk

For Ubuntu 12.04, you can install the oneiric version, but it will complain about 2 unmet dependencies. 
You can download those dependencies from here: http://packages.ubuntu.com/oneiric/allpackages. Then it will install.

running it
==========

Windows: navigate to the source code directory with cmd and run ppython pavara.py

Macs: navigate to the source code directory in a terminal and run ppython pavara.py

Linux: navigate to the source code directory in a terminal and run python pavara.py

roadmap
=======
* * * 
Maps
----
*   **port skybox from JME3 code**
*   **legacy map converter**
	*   add conversion for
		*   domes
		*   rounded rects
*   **map syntax**
	*   need definitions for
        *   level description
		*   lighting
		*   per-level logic
		*   fields/areas
		*   goodies
		*   custom shapes
		
Graphics
--------
###hi priority
*   **walker animations**
	*   seperate animations for `walk, stand, crouched_walk, crouch, airbourne_walk`
	*   animation blending based on crouch/walk factor, physics forces, and terrain
*   **dynamic model coloring**
    *   vertex recoloring
    	*	figure out head model coloring

###lo priority
*   **updated assets needed**
    *   walker(s) (export bobski's model)
	*   missile/grenade/plasma
	*   unigoody
*   **shadows**
    *   directional soft shadow mapping
*   **particle effects**
	* explosions
	
Networking
----------
*   **game object distribution and sync**
*   **server tracking**
*   **game metadata distribution (chat/level and asset distribution)**

Physics
-------
*   **bullet physics**
    *   same engine as JME3 clone
    *   need collision objects for all map objects -> bullet collision 'world'
    *   need custom hector 'kinematic' character controller (example: https://github.com/peterpodgorski/panda3d-bullet-kcc)
    *   integrate with animations
*   or, **panda physics manager**
    *   must create collision polys for map from primitives (Quads preferred over Tris)
    *   implement CollisionTraverser and CollisionHandlerQueue
    *   build hector controller from scratch, add collision meshes to model in Blender
    
User Interface
--------------
either:
*   2d rendering in Panda3d context, or
*   wxPython/window manager windows for configuration/setup and Panda3d context for gameplay
