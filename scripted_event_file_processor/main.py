import re
import json
import logging
from typing import List

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# this needs to be generalized
legend = {
    "g": {"name": "grab", "type": "playthrough"},
    "se": {"name": "smoke_emitter", "type": "toggle"},
    "lff": {"name": "lighter_flick_fail", "type": "playthrough"},
    "lfs": {"name": "lighter_flick_success", "type": "playthrough"},
    "cb": {"name": "cigarette_burn", "type": "toggle"},
    "cl": {"name": "cigarette_light", "type": "toggle"},
    "bs": {"name": "blowing_smoke", "type": "toggle"},
    "cs": {"name": "cigarette_smoke", "type": "toggle"},
    "sa": {"name": "smoke_animation", "type": "playthrough"},
    "in": {"name": "inhale", "type": "playthrough"},
    "ex": {"name": "exhale", "type": "playthrough"}
}

def get_layout_blocks(file_path: str) -> List[str]:
    logging.info(f"Starting to process file: {file_path}")

    try:
        # Open the file and read its contents
        with open(file_path, 'r') as file:
            input_string = file.read()
        logging.debug(f"File read successfully. Total length of content: {len(input_string)} characters.")
    
    except Exception as e:
        logging.error(f"Failed to read the file {file_path}: {e}")
        return []

    # Using the updated regex to extract blocks between lines that only contain 'x' followed by dashes
    try:
        blocks = re.findall(r"^x-+\n(.*?)^x-+|(?=\Z)", input_string, re.MULTILINE | re.DOTALL)
        logging.debug(f"Extracted {len(blocks)} blocks using regex.")
    except Exception as e:
        logging.error(f"Error during regex processing: {e}")
        return []

    layout_blocks = []
    for block in blocks:
        if block.strip():  # Only append non-empty blocks
            layout_blocks.append(block.strip())
            logging.debug(f"Added block with length {len(block.strip())} characters.")

    logging.info(f"Total number of layout blocks found: {len(layout_blocks)}")
    return layout_blocks


def parse_event_layout(file_path):
    logging.debug(f"Parsing event layout from file: {file_path}")
    events = []

    # logging.debug(f"File read successfully. Total lines: {len(lines)}")

    timeline_start = None
    frame_offset = None

    layout_blocks : List[str] = get_layout_blocks(file_path)

    for layout_block in layout_blocks:

        lines = layout_block.splitlines()

        for i, line in enumerate(lines):
            if "| timeline" in line:
                timeline_start = i
                logging.debug(f"Found timeline start at line: {i}")
            if "frame:" in line:
                frame_line = lines[i]
                frame_offset = int(re.search(r"frame:\s+(\d+)", frame_line).group(1))
                logging.debug(f"Found frame offset: {frame_offset}")
                break

        if timeline_start is None:
            logging.error("Timeline line not found in the file")
            raise ValueError("Timeline line not found in the file")

        # Parse event lines
        for i, line in enumerate(lines[:timeline_start]):
            line = line.strip()

            if not line or line.startswith("| comments"):
                logging.debug(f"Skipping empty or comment line at index {i}: {line}")
                continue

            # at this point its guarenteed that we're working on a event line

            event_matches = re.finditer(r"(\*|<|>)([a-z]+)", line)
            for match in event_matches:
                action_type, key = match.groups()
                time_position = match.start() - len("| events     | ")
                logging.debug(f"debugging {frame_offset}, {time_position}")
                frame_time = frame_offset + time_position

                logging.debug(f"Processing event: {action_type}{key} at time position {time_position}, frame time {frame_time}")

                if key not in legend:
                    logging.error(f"Unknown event key '{key}' in the layout at line {i}")
                    raise ValueError(f"Unknown event key '{key}' in the layout")

                event_info = legend[key]
                event_name = event_info["name"]
                event_type = event_info["type"]

                if action_type == "*":  # Playthrough event
                    action = "playthrough"
                elif action_type == ">":  # Toggle on
                    action = "toggle_on"
                elif action_type == "<":  # Toggle off
                    action = "toggle_off"
                else:
                    logging.error(f"Unknown action type '{action_type}' at line {i}")
                    raise ValueError(f"Unknown action type '{action_type}'")

                event = {
                    "name": event_name,
                    "time": frame_time,
                    "action": action
                }
                logging.debug(f"Adding event: {event}")
                events.append(event)

    logging.debug(f"Total events parsed: {len(events)}")
    return {"events": events}

def write_to_json(output_path, data):
    logging.debug(f"Writing parsed data to JSON file: {output_path}")
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=4)
    logging.info(f"Data successfully written to {output_path}")

if __name__ == "__main__":
    input_file = "smoking_event.txt"  
    output_file = "events.json"       

    logging.info("Starting event layout parsing")
    try:
        parsed_events = parse_event_layout(input_file)
        write_to_json(output_file, parsed_events)
        logging.info(f"Events successfully written to {output_file}")
    except Exception as e:
        logging.exception("An error occurred while processing the event layout.")
