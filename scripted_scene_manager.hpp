#ifndef SCRIPTED_SCENE_MANAGER_HPP
#define SCRIPTED_SCENE_MANAGER_HPP

#include <string>
#include <map>
#include <vector>
#include <glm/glm.hpp>
#include <nlohmann/json.hpp>

#include "sbpt_generated_includes.hpp"

using json = nlohmann::json;

class ScriptedSceneManager {
  public:
    ScriptedSceneManager(const std::string &scripted_scene_json_path);

    void run_scripted_events(double ms_curr_time,
                             std::function<void(double, const json &, const json &)> scripted_events);

  private:
    json prev_state;
    json curr_state;
    json changes;
    unsigned int changes_index;
};

#endif // SCRIPTED_SCENE_MANAGER_HPP
