------------------- help -------------------------------------------------------------------------------------------------------------
|
| Structure of the event layout system:
|
|   - The structure of the event layout system is a simple timeline with various channels. 
|   - The bottom two channels always consist of a timeline and a frame count specifying the current frame offset, it looks like this:
|
|
|     | timeline   | |----|----|----|----|----|----|----|----|----|----|----|----|----|----|----|----|----|----|----|----|
|     | frame: 100 | 0----5----10---15---20---25---30---35---40---45---50---55---60---65---70---75---80---85---90---95---100
|
|
|   - You will never have to modify these two lines. The lines above the bottom two are user created and can be event channels or comment channels
|     there can be any number of event or comment channels in any order, event channels are processed by the script whereas comment channels are used 
|     to clarify and mark out high level ideas so that its easier to understand the event layout.
|
| Creating Events:
|
|   - first make sure that the event exists in the legend
|   - then go to the timeline and then add the event
|   - if the event is a toggle event then to start the event at A and end the event at B with key X use the following syntax:
|
|                  >X                       <X
|             |----|----|----|----|----|----|----|----|
|                  A                        B
|
|   - if the event is a playthrough event with start time A with key Y then you just have to do this:
|
|                                 *Y
|             |----|----|----|----|----|----|----|----|
|                                 A
|
|
-----------------------------------------------------------------------------------------------------------------------------------------
