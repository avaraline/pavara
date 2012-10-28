pavara
======

A game inspired by the classic Mac game.

* * *

roadmap
=======

Maps
----
###high priority
*   **port celestials from JME3 code**
*   **legacy map converter**
	*   add conversion for
		*   domes
		*   rounded rects
###low priority
*   **map syntax**
	*   need definitions/implementation for
        *   level description
		*   per-level logic/scripting
		*	freeSoild/Solid/wallDoor/Door etc.
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
	* explosions
	* missle/lazer trails
	
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
*	**game data**: setup, types, start/end conditions
	
Sound
-----
###low priority
*	**doppler effect/stereo positioned playback**
*	**updated assets**
	*	plasma/misle/grenade loop
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