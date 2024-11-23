#include "scripted_scene_manager.hpp"

#include <algorithm>
#include <fstream>
#include <iostream>

using json = nlohmann::json;

ScriptedSceneManager::ScriptedSceneManager(const std::string &scripted_scene_json_path) : changes_index{0} {
    std::ifstream file(scripted_scene_json_path);
    json scripted_scene;
    file >> scripted_scene;

    prev_state = scripted_scene["state"];
    curr_state = scripted_scene["state"];
    changes = scripted_scene["changes"];

    if (!changes.is_array()) {
        throw std::runtime_error("Error parsing scripted scene!");
    }
    std::sort(changes.begin(), changes.end(), [](const nlohmann::json &this_change, const nlohmann::json &that_change) {
        return this_change["time"] < that_change["time"];
    });
}

void ScriptedSceneManager::run_scripted_events(
    double ms_curr_time, std::function<void(double, const json &, const json &)> scripted_events) {
    prev_state = curr_state;

    while (changes_index < changes.size() && changes[changes_index]["time"] <= ms_curr_time) {
        for (const auto [key, val] : changes[changes_index]["change"].items()) {
            std::cout << "[scene script] " << key << " -> " << val << std::endl;
            curr_state[key] = val;
        }
        changes_index++;
    }

    scripted_events(ms_curr_time, curr_state, prev_state);
}
