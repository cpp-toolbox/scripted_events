from enum import Enum
from typing import Tuple, List, Dict
from collections import defaultdict
from math_utils.main import get_decimal_part, round_to_decimal
from text_utils.main import generate_unique_abbreviation, insert_and_clobber
from collection_utils.main import are_elements_unique
from user_input.main import *
import logging
import os
import json

def min_channels_with_mapping(intervals: List[Tuple[int, int]]) -> Tuple[int, Dict[Tuple, int]]:
    """
    Find the minimal number of channels required and return the mapping of intervals to channels.

    :param intervals: List of intervals of the form [a, b] where a <= b
    :return: Tuple containing the minimal number of channels and a mapping of intervals to channels
    """
    if not intervals:
        return 0, {}

    # Sort intervals by start time and keep their original indices
    indexed_intervals = sorted(enumerate(intervals), key=lambda x: x[1][0])

    # Use a min-heap to keep track of end times of intervals in active channels
    # Each heap element is a tuple (end_time, channel)
    import heapq
    heap = []
    channel_mapping = {}
    next_channel = 0

    for original_index, (start, end) in indexed_intervals:
        # If the earliest end time is less than or equal to the start time of the current interval,
        # we can reuse its channel
        if heap and heap[0][0] <= start:
            _, channel = heapq.heappop(heap)
        else:
            # Otherwise, assign a new channel
            channel = next_channel
            next_channel += 1

        # Assign the current interval to the channel and push its end time onto the heap
        channel_mapping[tuple(intervals[original_index])] = channel
        heapq.heappush(heap, (end, channel))

    # The number of channels required is the number of unique channels used
    return next_channel, channel_mapping


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Action(Enum):
    PLAYTHROUGH = "playthrough"
    TOGGLE_ON = "toggle_on"
    TOGGLE_OFF = "toggle_off"

class Comment:
    def __init__(self, contents: str, time: float):
        self.contents = contents
        self.time = time

class Event: 
    def __init__(self, uid: str, name: str, time: float, action: Action):
        self.uid = uid
        self.name = name
        self.time = time
        self.action = action

class Timeline:
    def __init__(self, frame_unit=1,num_time_units_per_timeline_segment=10, num_subdivisions_per_time_unit =10):
        self.frame_unit = frame_unit  # The duration of one frame unit in seconds
        self.num_time_units_per_timeline_segment = num_time_units_per_timeline_segment # Duration of one segment in seconds
        self.num_subdivisions_per_time_unit = num_subdivisions_per_time_unit  # Number of dashes per segment
        self.events : List[Event] = []  # List to store events
        self.comments : List[Comment] = [] 
    
    


    def get_current_event_uids(self) -> Dict[str, str]:
        uid_to_event_name = {}
        for e in self.events:
            uid_to_event_name[e.uid] = e.name
        return uid_to_event_name

    def add_comment(self, comment: str, time: float):
        self.comments.append(Comment(comment, time))

    def add_event_automatic_uid(self, name: str, time: float, action: Action):
        uid = generate_unique_abbreviation(self.get_current_event_uids(), name)
        self.add_event(uid, name, time, action)

    def add_event(self, uid: str, name: str, time: float, action: Action):
        for e in self.events:
            if e.uid == uid and e.name != name:
                print("you tried to add an event with the same uid as another event but with a different name since uid -> event name mappings must be unique, this is a problem")
                return

        self.events.append(Event(uid, name, time, action))


    def convert_time_to_segment_and_dash_index(self, time: float) -> Tuple[int, int]:
        """
        Converts a given time to the corresponding timeline segment index and dash index.

        Parameters:
            time (float): The time to convert.

        Returns:
            Tuple[int, int]: The timeline segment index and dash index.
        """
        logger.info(f"Converting time: {time}")

        timeline_segment_index = int(time / self.num_time_units_per_timeline_segment)
        logger.debug(f"Calculated timeline_segment_index: {timeline_segment_index}")

        time_mod_segment = time % self.num_time_units_per_timeline_segment

        subinterval_decimal = 1 / self.num_subdivisions_per_time_unit
        logger.debug(f"Subinterval decimal: {subinterval_decimal}")

        rounded_to_subinterval_time = round_to_decimal(time_mod_segment, subinterval_decimal)
        logger.debug(f"Rounded to subinterval time: {rounded_to_subinterval_time}")

        total_num_units = int(rounded_to_subinterval_time)
        logger.debug(f"Total number of units: {total_num_units}")

        left_over_units: float = get_decimal_part(rounded_to_subinterval_time)
        logger.debug(f"Left over units: {left_over_units}")

        left_over_dash_index = int(left_over_units * self.num_subdivisions_per_time_unit)
        logger.debug(f"Left over dash index: {left_over_dash_index}")

        dash_index = total_num_units * self.num_subdivisions_per_time_unit + left_over_dash_index
        logger.debug(f"Calculated dash index: {dash_index}")

        logger.info(f"Conversion result - Timeline Segment Index: {timeline_segment_index}, Dash Index: {dash_index}")

        return timeline_segment_index, dash_index


    def generate_events_line_for_timeline_segment(self, segment_events) -> List[str]:
        logger.info("Generating events line for timeline segment.")
        
        # Initialize the event line with dashes, as a string
        event_line = "| events     | " + "-" * (self.num_time_units_per_timeline_segment * self.num_subdivisions_per_time_unit)
        total_subdivisions = (self.num_time_units_per_timeline_segment * self.num_subdivisions_per_time_unit)
        logger.debug(f"Initialized event line with total_subdivisions: {total_subdivisions}")

        # TODO tomorrow build out this code in a similar way but first we have to pair up matching > < tags into their own intervals.

        # NOTE: this assumes that each interval is associated with one UID which is bad! we need to add other identifying information to make this work
        event_interval_to_event_str = {}
        event_intervals = []
        action_type_to_event: Dict[Action, List[Event]] = {}

        # Loop through each event and place it at the correct index
        for e in segment_events:
            logger.debug(f"Processing event: {e}")
            if e.action not in action_type_to_event:
                action_type_to_event[e.action] = []
            action_type_to_event[e.action].append(e)

        # Handle PLAYTHROUGH actions
        for event in action_type_to_event.get(Action.PLAYTHROUGH, []):
            logger.debug(f"Processing PLAYTHROUGH event: {event}")
            event_string = f"*{event.uid}"
            segment_index, dash_index = self.convert_time_to_segment_and_dash_index(event.time)
            event_interval = (dash_index, dash_index + len(event_string))
            logger.debug(f"PLAYTHROUGH event string: {event_string}, interval: {event_interval}")
            event_intervals.append(event_interval)
            event_interval_to_event_str[event_interval] = event_string

        # Handle TOGGLE_ON actions
        processed_toggle_off_events = []
        for event in action_type_to_event.get(Action.TOGGLE_ON, []):
            logger.debug(f"Processing TOGGLE_ON event: {event}")
            segment_index, dash_index = self.convert_time_to_segment_and_dash_index(event.time)
            event_string = f">{event.uid}"
            toggle_off_event = None
            end_event_dash_index = None

            for other_event in action_type_to_event.get(Action.TOGGLE_OFF, []):
                logging.debug(f"comparing: {other_event.uid} {event.uid}")
                if other_event.uid == event.uid and other_event not in processed_toggle_off_events:
                    _, end_event_dash_index = self.convert_time_to_segment_and_dash_index(other_event.time)
                    toggle_off_event = other_event
                    processed_toggle_off_events.append(toggle_off_event)
                    break
            
            if toggle_off_event is None:
                event_interval = (dash_index, total_subdivisions - 1)
                event_string += "~" * (total_subdivisions - dash_index)
                logger.warning(f"No matching TOGGLE_OFF event for TOGGLE_ON event UID: {event.uid}")
            else:
                event_interval = (dash_index, end_event_dash_index)
                num_spaces_required = (end_event_dash_index - dash_index - len(event_string)) 
                event_string += "~" * num_spaces_required  + f"<{toggle_off_event.uid}"

            logger.debug(f"TOGGLE_ON event string: {event_string}, interval: {event_interval}")
            event_interval_to_event_str[event_interval] = event_string
            event_intervals.append(event_interval)

        num_channels_required, interval_to_channel = min_channels_with_mapping(event_intervals)
        logger.info(f"Number of channels required: {num_channels_required}")

        event_lines = [" " * self.num_subdivisions_per_time_unit * self.num_time_units_per_timeline_segment] * num_channels_required
        for event_interval, channel in interval_to_channel.items():
            event_str = event_interval_to_event_str[event_interval]
            logger.debug(f"Placing event '{event_str}' in channel {channel}, interval: {event_interval}")
            event_lines[channel] = insert_and_clobber(event_lines[channel], event_str, event_interval[0])

        for i in range(len(event_lines)):
            event_lines[i] = "| events     | " + event_lines[i]
            logger.debug(f"Event line {i}: {event_lines[i]}")

        logger.info("Finished generating events lines.")
        return event_lines

    def generate_comment_lines(self, curr_segment_comments: List[Comment]) -> List[str]:
        comment_interval_to_comment_contents = {}
        comment_intervals = []
        for comment in curr_segment_comments:
            contents = comment.contents
            comment_time = comment.time
            _, comment_dash_index = self.convert_time_to_segment_and_dash_index(comment_time)
            comment_dash_index_end = comment_dash_index + len(contents)
            comment_interval = (comment_dash_index, comment_dash_index_end)
            comment_intervals.append(comment_interval)
            # we require that the comment intervals are unique for now
            # this is so that we can map back to what comment is associated with whcih interval
            # this is bad but if it ever becomes an actual problem we'll fix it at some point
            assert comment_interval not in comment_interval_to_comment_contents
            comment_interval_to_comment_contents[comment_interval] = contents

        num_channels_required, interval_to_channel = min_channels_with_mapping(comment_intervals) 

        comment_lines = [" " * self.num_subdivisions_per_time_unit * self.num_time_units_per_timeline_segment] * num_channels_required
        for comment_interval, channel in interval_to_channel.items():
            contents = comment_interval_to_comment_contents[comment_interval]
            comment_lines[channel] = insert_and_clobber(comment_lines[channel], contents, comment_interval[0])


        for i in range(len(comment_lines)):
            comment_lines[i] = "| comments   | " + comment_lines[i]

        return comment_lines


    # TODO was just pasted this in for debuggging because only seeing one timeline segment
    def generate_timeline(self) -> str:
        logging.info("Starting to generate the timeline.")
        timeline_output = []
        
        # Calculate how many segments we need
        max_event_time = max([e.time for e in self.events], default=0)
        max_comment_time = max([c.time for c in self.comments], default=0)
        max_time = max(max_event_time, max_comment_time)
        num_segments = int((max_time // self.num_time_units_per_timeline_segment) + 1)
        
        logging.debug(f"Calculated max_event_time: {max_event_time}, max_comment_time: {max_comment_time}, max_time: {max_time}, num_segments: {num_segments}.")
        
        # Generate the timeline for each segment
        for segment_index in range(num_segments):
            logging.debug(f"Processing segment {segment_index}.")
            timeline_output.append("x--------------------------------------------------------------------------------------------------------------------")
            
            # Find all events and comments for the current segment
            segment_events = [e for e in self.events if int(e.time // self.num_time_units_per_timeline_segment) == segment_index]
            segment_comments = [c for c in self.comments if int(c.time // self.num_time_units_per_timeline_segment) == segment_index]
            
            logging.debug(f"Found {len(segment_events)} events and {len(segment_comments)} comments for segment {segment_index}.")
            
            # Add comments (names of events in the current segment)
            comment_lines = self.generate_comment_lines(segment_comments)
            timeline_output.extend(comment_lines)
            logging.debug(f"Added {len(comment_lines)} comment lines for segment {segment_index}.")
            
            # Add event actions in the current segment
            event_lines = self.generate_events_line_for_timeline_segment(segment_events)
            timeline_output.extend(event_lines)
            logging.debug(f"Added {len(event_lines)} event lines for segment {segment_index}.")
            
            # Add timeline frame (with dashes per segment)
            timeline_line = "| timeline   | " + ("|" + "-" * (self.num_subdivisions_per_time_unit - 1)) * self.num_time_units_per_timeline_segment
            timeline_output.append(timeline_line)
            logging.debug(f"Added timeline frame for segment {segment_index}.")
            
            # Add frame markers with dashes between them
            frame_line = f"| frame: {segment_index * self.num_time_units_per_timeline_segment:03d} | "
            frame_line += "".join([str(i) + "-" * (self.num_subdivisions_per_time_unit - 1) for i in range(self.num_time_units_per_timeline_segment)])
            timeline_output.append(frame_line)
            logging.debug(f"Added frame line for segment {segment_index}.")
            
            # Add separator between segments
            timeline_output.append("x--------------------------------------------------------------------------------------------------------------------")
            logging.debug(f"Added separator for segment {segment_index}.")
        
        # Combine all lines
        result = "\n".join(timeline_output)
        logging.info("Timeline generation completed.")
        return result
    
    def generate_legend(self):
        processed_events = []
        output = "legend\n"
        for e in self.events:
            print("DEbOGG", e.name, e.uid, e.action, e.time)
            event_type = "toggle" if "toggle" in e.action.value else "playthrough"
            event_repr = (e.uid, event_type)
            if event_repr not in processed_events:
                output += f"- {e.name}\n"
                output += f"  - key: {e.uid}\n"
                output += f"  - type: {event_type}\n"
                processed_events.append(event_repr)

        output += "frame_unit: 1s\n\n"

        return output

    def generate_script_event_file_contents(self) -> str:
        file_contents = ""
        file_contents += self.generate_legend()
        file_contents += self.generate_timeline()
        return file_contents


# Example usage:
timeline = Timeline()

# Add some events
timeline.add_comment("grab", 0)
timeline.add_event("gcccccccccccc", "grab cigs", 0, Action.PLAYTHROUGH)
timeline.add_comment("lightttttttttt", 1)
timeline.add_event("liuuuuuu", "light it up", 1, Action.PLAYTHROUGH)
timeline.add_comment("burnnnnnnn", 2)
timeline.add_event("csb", "cig starts burning", 2, Action.TOGGLE_ON)
timeline.add_event("csb", "cig starts burning", 3, Action.TOGGLE_OFF)

timeline.add_comment("inhaleeeeeeeeeeeee", 5)
timeline.add_event("iiiiiiiiiiii", "inhale", 5, Action.PLAYTHROUGH)
timeline.add_comment("exhale", 6.5)
timeline.add_event("exxxxxxxxxxxxxx", "exhale", 6.5, Action.PLAYTHROUGH)
timeline.add_comment("fresh boy", 16.0002)
timeline.add_event("nb", "newboy", 16.0002, Action.PLAYTHROUGH)

# Generate timeline output
timeline_output = timeline.generate_timeline()
print(timeline_output)



################



# Example usage:
intervals = [(1, 3), (2, 4), (3, 5), (7, 8), (6, 9)]
num_channels, mapping = min_channels_with_mapping(intervals)
print(f"Minimum number of channels required: {num_channels}")
print("Mapping of intervals to channels:")
for interval, channel in mapping.items():
    print(f"Interval {interval} -> Channel {channel}")

################


