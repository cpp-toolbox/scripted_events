#ifndef SCRIPTED_SCENE_MANAGER_HPP
#define SCRIPTED_SCENE_MANAGER_HPP

#include <string>
#include <map>
#include <unordered_set>
#include <vector>
#include <glm/glm.hpp>
#include <nlohmann/json.hpp>

#include "sbpt_generated_includes.hpp"

using json = nlohmann::json;

class ScriptedEvent {
  public:
    ScriptedEvent() {};
    ScriptedEvent(const std::string &scripted_event_json_path);

    void load_in_new_scripted_event(const std::string &scripted_event_json_path);

    void run_scripted_events(double curr_time_sec,
                             const std::unordered_map<std::string, std::function<void(bool, bool)>> &event_callbacks);

    void reset_processed_state();

  private:
    struct PlaythroughEvent {
        std::string name;
        double time;
    };

    struct TogglableEvent {
        std::string name;
        double start_time;
        double end_time;

        std::string get_str_repr() const {
            return "event: " + name + " (" + std::to_string(start_time) + ", " + std::to_string(end_time) + ")";
        }
    };

    // TODO using strings here is bad when you have multiple events which could overlap
    // that also using the same event name, this edge case needs to be handled robustly in the future
    std::unordered_set<std::string> processed_playthrough_events;

    std::vector<PlaythroughEvent> playthrough_events;
    std::vector<TogglableEvent> togglable_events;

    std::unordered_map<std::string, TemporalBinarySignal> togglable_event_to_tbs;

    size_t playthrough_event_index = 0; ///< Index of the next event to process
};

#endif // SCRIPTED_SCENE_MANAGER_HPP
