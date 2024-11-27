# scripted_event_manager
A scripted event manager is a system which allows you to sync the usage of various systems at once.

This type of system becomes useful when you have specific events you want to model when doing it programatically would be too painstaking.

The real life analogue of this is like a movie crew that has special effects that need to be run at certain times when recording a scene.

# examples
* syncing sounds up to an animation rather than having a fixed length audio file for an entire animation
  * You have a reload animation and at certain points in time you use distinct sound files this allows you to tweak animation or sounds individually without breaking eachother
* syncing up lighting and particle emitters to an animation
  * You have a lawnmower and it takes 3 tugs to start it so you run the animation 3 times sequentially before getting into the working state, each time the tug animation plays we also want a sound to play and smoke emitters to run
* syncing up physics to the exact moment the explosion animation runs
* moving the camera to the correct position at a certain point of time during an animation
* cutscenes

# events
Events usually come in two main forms, a toggle event and a playthrough event

## toggle event
An event that can be toggled and has a duration, think of these like switches that can be turned on or off, when on it continuously does what its supposed to do. Examples of this could be lighting and particle emitters.

## playthrough events
A one time/singular event with no set duration. The easiest way to understand this is in the context of playing sounds, when you fire a gun you want to play the fire sound, you don't care how long it lasts because the duration is already baked into the sound itself, so you just want to play it and not ever care about turning it on or off, as it doesn't even have a state like that. 

Note: The easiest way to compare these types of events are that toggle events are those in which you must manually control its duration, and playthrough events are those which handle their own duration themselves, so toggle events are like playthrough events except you're in charge of when they end.
