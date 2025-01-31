#include "scripted_scene_manager.hpp"

#include <algorithm>
#include <fstream>
#include <iostream>

using json = nlohmann::json;

ScriptedEvent::ScriptedEvent(const std::string &scripted_scene_json_path) : playthrough_event_index{0} {
    load_in_new_scripted_event(scripted_scene_json_path);
}

void ScriptedEvent::load_in_new_scripted_event(const std::string &scripted_event_json_path) {
    playthrough_events.clear();
    togglable_events.clear();
    // Open and parse the JSON file
    std::ifstream file(scripted_event_json_path);
    if (!file.is_open()) {
        throw std::runtime_error("Unable to open the scripted scene file!");
    }

    json scripted_scene;
    file >> scripted_scene;

    // Validate the "events" field
    const auto &events_json = scripted_scene["events"];
    if (!events_json.is_array()) {
        throw std::runtime_error("Error parsing scripted scene: 'events' field must be an array!");
    }

    // Process each event
    for (const auto &event_json : events_json) {
        const std::string type = event_json["type"];
        const std::string name = event_json["name"];

        if (type == "playthrough") {
            double time = event_json["time"];
            playthrough_events.push_back({name, time});
        } else if (type == "toggle") {
            double start_time = event_json["start_time"];
            double end_time = event_json["end_time"];
            togglable_events.push_back({name, start_time, end_time});
        } else {
            throw std::runtime_error("Unknown event type: " + type);
        }
    }

    // Sort playthrough events by time
    std::sort(playthrough_events.begin(), playthrough_events.end(),
              [](const PlaythroughEvent &a, const PlaythroughEvent &b) { return a.time < b.time; });

    // Sort togglable events by start_time
    std::sort(togglable_events.begin(), togglable_events.end(),
              [](const TogglableEvent &a, const TogglableEvent &b) { return a.start_time < b.start_time; });
}

void ScriptedEvent::reset_processed_state() {
    playthrough_event_index = 0;
    processed_playthrough_events.clear();
}

void ScriptedEvent::run_scripted_events(
    double curr_time_sec, const std::unordered_map<std::string, std::function<void(bool, bool)>> &event_callbacks) {

    // Process playthrough events based on current time
    // this is like a moving time ticker, event index doesn't get reset because
    // there's no need to check events coming before because they have a smaller time
    while (playthrough_event_index < playthrough_events.size() &&
           playthrough_events[playthrough_event_index].time <= curr_time_sec) {
        const auto &event = playthrough_events[playthrough_event_index];

        auto it = event_callbacks.find(event.name);
        if (it != event_callbacks.end()) {
            // Ensure playthrough events are only triggered once
            if (processed_playthrough_events.find(event.name) == processed_playthrough_events.end()) {
                it->second(true, true);
                processed_playthrough_events.insert(event.name);
            }
        } else {
            std::cerr << "[event script] No callback registered for playthrough event: " << event.name << std::endl;
        }

        playthrough_event_index++;
    }

    // Process toggle events
    for (const auto &toggle_event : togglable_events) {

        auto &curr_tbs = togglable_event_to_tbs[toggle_event.get_str_repr()];
        bool event_is_toggled = toggle_event.start_time <= curr_time_sec and curr_time_sec <= toggle_event.end_time;

        if (event_is_toggled) {
            curr_tbs.set_on();
        } else {
            curr_tbs.set_off();
        }
        curr_tbs.process();

        auto it = event_callbacks.find(toggle_event.name);
        if (it != event_callbacks.end()) {
            if (event_is_toggled) {
                it->second(curr_tbs.is_just_on(), false);
            } else {
                if (curr_tbs.is_just_off()) {
                    // this is the "last_call of this callback
                    it->second(false, true);
                }
            }
        } else {
            std::cerr << "[event script] No callback registered for toggle event: " << toggle_event.name << std::endl;
        }
    }
}
