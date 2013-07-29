<table>
	<tr>
		<td>
			<h1>pavara</h1><br/>
			A game insprired by the classic mac game
		</td>
		<td>
			<img src="https://dl.dropbox.com/u/38430353/indra_thumb.jpg" alt="Indra by rherriman"/>
		</td>
	</tr>
</table>

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

* * *
roadmap
=======

Maps
----
###high priority
*   **legacy map converter**
	*   add conversion for
		*   domes
		*	fields
		*	walldoors
		*	teleporters

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
		* 	enemies

Graphics
--------
###high priority
*   **walking animation**
    *   implement correct walk cycle

*	**deferred shading, bloom, transparency**
	*	integrate shadows (directional higher priority than shadows from point-lights)

###low priority
*   **updated assets**
	*   finalize projectile models
	*   unigoody (or placeholder)
	*	scout
	*	pillbox or 'autoturret'
	*	"ball"
	*	mine
	*	guard/ufo/ai walker
*	triangle debris when walkers scrape walls

*   **particle effects**
	*	missle/lazer trails?
	*	environmental, e.g. precipitation?

Networking
----------
###high priority
*   **time travelling**
*	multiple physics simulations on the server/clients? ([discussion here](https://docs.google.com/document/d/1WPZOwmkIAJMAJXovGwdvVnahyb-7qaJY826McMYeMVo/))

###low priority
*   **server tracking**
*   **game metadata distribution (chat/level and asset distribution)**
*	**ladder**
*	**films hall of fame**

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
*	**game data**: setup, types, start/end conditions, game recording
*	**messages**: triggering and listening for simple events, both in XML and whatever scripting set up we use
*	**game modes**
	*	vanilla mode with baseline hull
	*	custom 'loadout' mode
	*	co-op firefight

Sound
-----
###low priority
*	**doppler effect**
*	**updated assets**
	*	plasma/missle/grenade loop
	*	kArticWind etc. replacements
	*	footstep sounds, goody sounds
	*	teleporter sounds
	*	xplosions

Physics (Bullet)
-------
###higher priority
*	**kinematic character controller**
	*	collision detection for damage and externally applied forces (explosions/weapons fire)
	*	impulse vertical height adjustment/crouching for hitting ground from free-fall
*	**ballistics**
	*	grenade lobbing!
	*	"smart" missle tracking
	*	walker energy, cannons, shield charging
	*	laser cannons
	*	splash/freesolid/laser damage/recoil

###lower priority
*	**other collidables**
	*	fields/areas
	*	kinematic map objects

User Interface
--------------
###lowest priority
*	**preliminary designs**
*	3d target reticules (finalize plasma/missile, draft grenade)
