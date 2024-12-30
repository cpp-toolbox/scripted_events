import re
import json
import logging
from typing import List, Dict

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to extract the legend as a string
def extract_legend(input_data: str) -> str:
    lines = input_data.splitlines()
    legend_lines = []
    for line in lines:
        if line.strip() == "----- event layout system start -----":
            break
        legend_lines.append(line)
    return "\n".join(legend_lines)

def parse_legend_to_dictionary(raw_legend_string: str) -> Dict:
    logging.info("Parsing legend string into dictionary")

    lines = raw_legend_string.splitlines()

    legend_dict = {}
    current_name = None
    key = None

    for line in lines:
        line = line.strip()
        logging.debug(f"Processing line: {line}")
        if line.startswith("-") and not line.startswith("- key") and not line.startswith("- type"):
            # Start of a new legend item
            current_name = line[2:].strip()
            logging.debug(f"Found legend item: {current_name}")
        elif line.startswith("- key:"):
            # Extract the key
            key = line.split(":", 1)[1].strip()
            logging.debug(f"Extracted key: {key}")
        elif line.startswith("- type:") and key is not None:
            # Extract the type and bind key to current_name
            type_value = line.split(":", 1)[1].strip()
            logging.debug(f"Extracted type: {type_value}")
            legend_dict[key] = {"name": current_name, "type": type_value}
            logging.info(f"Added to dictionary: key={key}, name={current_name}, type={type_value}")
            key = None  # Reset key after binding

    return legend_dict



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

def calculate_dash_duration(timeline_str: str, frame_unit: int) -> float:
    logging.debug("Starting calculation of dash duration.")
    
    try:
        # Find the position of the first frame marker after the first '|'
        start_bar_index = timeline_str.index("|") + 1  # Skip the first '|'
        logging.debug(f"Start searching after the first '|', starting at index {start_bar_index}.")
        
        # Find the first '0' and '1' after the first '|'
        start_index = timeline_str.index("0", start_bar_index)
        end_index = timeline_str.index("1", start_index)
        
        logging.debug(f"Found '0' at index {start_index}, '1' at index {end_index}.")
        
        # Count the dashes between the two frame markers
        dashes_between = timeline_str[start_index:end_index].count("-")
        
        logging.debug(f"Number of dashes between '0' and '1': {dashes_between}.")
        
        if dashes_between == 0:
            logging.error("No dashes found between '0' and '1'.")
            raise ValueError("No dashes found between '0' and '1'.")

        total_number_of_time_subdivisions = dashes_between + 1
        
        # Calculate the duration of one dash
        duration_per_dash = frame_unit / total_number_of_time_subdivisions
        
        logging.debug(f"Calculated duration per dash: {duration_per_dash} seconds.")
        
        return duration_per_dash
    
    except ValueError as e:
        logging.error(f"ValueError: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise


def parse_event_layout(file_path: str, legend: Dict) -> Dict:
    logging.debug(f"Parsing event layout from file: {file_path}")
    events = []

    # logging.debug(f"File read successfully. Total lines: {len(lines)}")

    timeline_start = None
    frame_offset = None

    timeline_segments : List[str] = get_layout_blocks(file_path)

    duration_of_tick = -1

    for timeline_segment in timeline_segments:

        lines = timeline_segment.splitlines()

        for i, line in enumerate(lines):
            if "| timeline" in line:
                timeline_start = i
                logging.debug(f"Found timeline start at line: {i}")
            if "frame:" in line:
                frame_line = lines[i]
                # TODO generalize this
                if (duration_of_tick == -1):
                    duration_of_tick = calculate_dash_duration(frame_line, 1)
                    print(f"The duration of one dash is {duration_of_tick} seconds.")
                frame_offset = int(re.search(r"frame:\s+(\d+)", frame_line).group(1))
                logging.debug(f"Found frame offset: {frame_offset}")
                break

        if timeline_start is None:
            logging.error("Timeline line not found in the file")
            raise ValueError("Timeline line not found in the file")

        # Parse event lines
        for i, line in enumerate(lines[:timeline_start]):
            print("DEBOGGGING", line)
            line = line.strip()

            if not line or line.startswith("| comments"):
                logging.debug(f"Skipping empty or comment line at index {i}: {line}")
                continue

            # at this point its guarenteed that we're working on a event line

            playthrough_matches = re.finditer(r"(\*)([A-Za-z]+)", line)
            toggle_matches = [(m.group(1), m.start(), m.end() - 1) for m in re.finditer(r">([A-Za-z0-9]+)~*.*?<\1", line)]

            for match in playthrough_matches:
                event_type, key = match.groups()
                frame_position = match.start() - len("| events     | ")
                frame_of_event = frame_offset + frame_position * duration_of_tick

                logging.debug(f"Processing event: {event_type}{key} at frame position {frame_position}, frame time {frame_of_event}")

                if key not in legend:
                    logging.error(f"Unknown event key '{key}' in the layout at line {i}")
                    raise ValueError(f"Unknown event key '{key}' in the layout")

                event_info = legend[key]
                event_name = event_info["name"]

                assert duration_of_tick != -1
                event = {
                    "name": event_name,
                    "time": frame_of_event ,
                    "type": "playthrough"
                }
                logging.debug(f"Adding event: {event}")
                events.append(event)

            for match in toggle_matches:
                key, start_time, end_time = match

                start_frame_pos = start_time - len("| events     | ")
                end_frame_pos = end_time - len("| events     | ")

                start_frame = frame_offset + start_frame_pos * duration_of_tick
                end_frame = frame_offset + end_frame_pos * duration_of_tick

                if key not in legend:
                    logging.error(f"Unknown event key '{key}' in the layout at line {i}")
                    raise ValueError(f"Unknown event key '{key}' in the layout")

                event_info = legend[key]
                event_name = event_info["name"]

                assert duration_of_tick != -1
                event = {
                    "name": event_name,
                    "start_time": start_frame,
                    "end_time": end_frame,
                    "type": "toggle"
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

def convert_scripted_event_file_to_json_file(scripted_event_file_path: str, json_output_path: str):
    logging.info("Starting event layout parsing")
    try:
        with open(scripted_event_file_path, 'r') as file:
            raw_legend = extract_legend(file.read())
            legend = parse_legend_to_dictionary(raw_legend)
            parsed_events = parse_event_layout(scripted_event_file_path, legend)
            write_to_json(json_output_path, parsed_events)
            logging.info(f"Events successfully written to {json_output_path}")
    except Exception as e:
        logging.exception("An error occurred while processing the event layout.")


from timeline import *

class TimelineCLI:
    def __init__(self):
        self.timeline = Timeline()

    def add_comment(self):
        comment = input("Enter comment: ")
        time = float(input("Enter time for the comment: "))
        self.timeline.add_comment(comment, time)
        print("Comment added successfully.")

    def add_event(self):
        uid = input("Enter event UID: ")
        name = input("Enter event name: ")
        time = float(input("Enter time for the event: "))
        action = Action(select_options(["toggle_on", "toggle_off", "playthrough"], True)[0])
        self.timeline.add_event(uid, name, time, action)
        print("Event added successfully.")

    def add_event_automatic_uid(self):
        name = input("Enter event name: ")
        time = float(input("Enter time for the event: "))
        action = Action(select_options(["toggle_on", "toggle_off", "playthrough"], True)[0])
        self.timeline.add_event_automatic_uid(name, time, action)
        print("Event with automatic UID added successfully.")

    def print_timeline(self):
        timeline_data = self.timeline.generate_script_event_file_contents()
        print("\nGenerated Timeline:\n")
        print(timeline_data)

    def write_timeline_to_file(self):
        file_path = input("Enter file path to save the timeline: ")
        timeline_data = self.timeline.generate_script_event_file_contents()
        with open(file_path, "w") as file:
            file.write(timeline_data)
        print(f"Timeline written to {file_path}.")

    def convert_scripted_event_file_to_json_file(self):
        se_file_path = input("Enter file path to scripted event file: ")
        json_file_path = input("Enter file path to json file: ")
        convert_scripted_event_file_to_json_file(se_file_path , json_file_path)
        print(f"Json written to {json_file_path}.")


    def import_marker_file(self):
        file_path = input("Enter path to marker file: ")
        if not os.path.exists(file_path):
            print("File not found.")
            return

        with open(file_path, "r") as file:
            lines = file.readlines()

        # Process each line in the file, skipping the header
        for line in lines[1:]:  # Skip the first line (header)
            line = line.strip()  # Remove any leading/trailing whitespace
            if not line:  # Skip empty lines
                continue
            time, marker = line.split('\t')  # Split the line into time and comment

            action = None

            if marker[0] == ">": 
                action = Action.TOGGLE_ON

            if marker[0] == "<": 
                action = Action.TOGGLE_OFF

            if marker[0] == "*": 
                action = Action.PLAYTHROUGH

            self.timeline.add_event_automatic_uid(marker[1:], float(time), action)
            # self.timeline.add_comment(comment, float(time))  # Call the function with the processed values
        # Load markers into the timeline (this depends on your implementation)
        print(f"Marker file {file_path} imported successfully.")

    def import_scripted_event_file(self):
        file_path = input("Enter path to scripted event file: ")
        if not os.path.exists(file_path):
            print("File not found.")
            return

        with open(file_path, "r") as file:
            scripted_event_data = json.load(file)
        # Load scripted events into the timeline (this depends on your implementation)
        print(f"Scripted event file {file_path} imported successfully.")

    def run(self):
        while True:
            print("\nTimeline CLI")
            print("1. Add Comment")
            print("2. Add Event (manual UID)")
            print("3. Add Event (automatic UID)")
            print("4. Print Timeline")
            print("5. Write Timeline to File")
            print("6. Import Marker File")
            print("7. Import Scripted Event File")
            print("8. Import Existing scripted event file")
            print("9. Convert scripted event file to json file")
            print("10. Exit")

            choice = input("Enter your choice: ")

            if choice == "1":
                self.add_comment()
            elif choice == "2":
                self.add_event()
            elif choice == "3":
                self.add_event_automatic_uid()
            elif choice == "4":
                self.print_timeline()
            elif choice == "5":
                self.write_timeline_to_file()
            elif choice == "6":
                self.import_marker_file()
            elif choice == "7":
                self.import_scripted_event_file()
            elif choice == "8":
                print("not yet implemented")
                pass
            elif choice == "9":
                self.convert_scripted_event_file_to_json_file()
                break
            elif choice == "10":
                print("Exiting CLI. Goodbye!")
                break
            else:
                print("Invalid choice. Please try again.")

if __name__ == "__main__":
    cli = TimelineCLI()
    cli.run()

