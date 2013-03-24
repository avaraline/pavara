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

pavara depends on [Panda3d](http://www.panda3d.org/download.php?sdk&version=1.8.0).

Panda3d installer links: [Windows](http://www.panda3d.org/download/panda3d-1.8.0/Panda3D-1.8.0.exe), [Mac](http://www.panda3d.org/download/panda3d-1.8.0/Panda3D-1.8.0.dmg), [Linux (Ubuntu)](http://www.panda3d.org/download.php?platform=ubuntu&version=1.8.0&sdk).

Mac users also need the [NVidia CG toolkit](https://developer.nvidia.com/cg-toolkit). Mac users may also need an [X11 Server](http://xquartz.macosforge.org/trac) if one is not installed.

In Ubuntu 12.04, the `oneiric` version of Panda3d will complain about 2 unmet dependencies during installation. [Download these](http://packages.ubuntu.com/oneiric/allpackages) to install.

running
-------
The python script `map_test.py` must be run with the `ppython` command (provided by Panda3d) inside the source directory.

* Windows: open a new `cmd.exe`, `dir \Wherever\You\Saved\pavara` then `ppython map_test.py`

* Mac/Linux: open a new terminal and `cd /path/to/pavara/folder` followed by `ppython map_test.py`

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
		* 	enemies

Graphics
--------
###high priority
*   **walking animation**
    *   improvements
	*	work with colliision character to stop feet on terrain

*	**deferred shading, bloom, transparency**
	*	point lights on everything

###low priority
*   **updated assets**
	*   grenade model, finalize missle/plasma
	*   unigoody
	*	scout
	*	pillbox or 'autoturret'
	*	"ball"
	*	mine
	*	guard/ufo/ai walker
*	triangle debris when walkers scrape walls

*   **shadows**
    *   directional soft shadow mapping
*   **particle effects**
	*	missle/lazer trails?
	*	environmental, e.g. precipitation?

Networking
----------
###high priority
*   **time travelling**

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
	*	custom 'loadout' mode where several 'stats' are set using a fixed number of points enable you to select one or more balanced 'skills' based on the stats ???
		*	for example, in addition to the baseline hull
			* **agility** - increased top speed, decreased ammo capcity and armor, additional jump(s), wall jumps, floor sliding
			* **defensive** - increased armor, decreased speed, droppable auto-turret (pillbox), droppable mines, ???
			* **offensive** - increased ammo capacity, decreased armor, droppable remote motion sensor beacon, tele to scout, ???
	*	co-op firefight, maps would need hooks for enemy spawn points

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
	*	improve collision detection
	*	send messages to walker object for animation
	*	improve leg animation and IK to terrain
	*	vertical height adjustment/crouching for jumping
*	**ballistics**
	*	grenade lobbing
	*	"smart" missle tracking
	*	hector energy, cannons, shield charging
	*	laser cannons
		*	less energy = less shot power
		*	add something for the opposite situation? *arcing charge shot*: if cannons at 100% power, hold down button to charge a large 'arcing' shot, which, scaling with charge time, has the effect of 'jumping' to other players within range of the player struck by the original arc shot, doing a fraction of the damage for each 'jump'. this would drain your cannons completely and overcharging (and self-destruction) would be possible. could be 'skill'
	*	splash/freesolid/laser damage/recoil

###lower priority
*	**other collidables**
	*	fields/areas
	*	kinematic map objects

User Interface
--------------
###lowest priority
*	**preliminary designs**
*	3d target reticules
