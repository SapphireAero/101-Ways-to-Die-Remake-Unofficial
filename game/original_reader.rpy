# Route reader shared with the remake; public data contains no original story.

transform original_center_4_3:
    xysize (1440, 1080)
    xalign 0.5
    yalign 0.5

default original_choice_history = []

label original_hub:
    $ original_audio_stop()
    return

label original_script_reader:
    $ original_audio_stop()
    $ original_auxiliary_progress = {}
    $ original_scenario_call_stack = []
    $ original_gallery_replay_mode = False
    $ original_route_state = original_route_begin()
    if not original_route_state.get("calls"):
        jump original_linear_script_reader

    call original_story_video(original_opening_movie_path())

    $ original_scenario_name = PUBLIC_CATALOG["prologue"]
    call original_scenario_file_reader

    while not original_route_state.get("done"):
        $ original_route_call = original_route_next(original_route_state)
        if original_route_call is not None:
            $ original_scenario_name = original_route_call["scenario"]
            call original_scenario_file_reader
            $ original_route_result = _return
            if original_scenario_name in ORIGINAL_ENDING_UNLOCK_SCENARIOS:
                call original_story_video(original_ending_movie_path(ORIGINAL_ENDING_UNLOCK_SCENARIOS.index(original_scenario_name)))
            $ original_route_apply_choice(original_route_state, original_route_result)

    "路线已经播放完毕。"
    jump original_hub

label original_linear_script_reader:
    $ original_lines = original_load_script_lines()
    $ original_background_events = original_load_background_events()
    $ original_choice_events = original_load_choice_events()
    $ original_choice_history = []
    if not original_lines:
        "没有找到 demo/data/pure_script.txt。"
        jump original_hub

    scene black
    with dissolve

    $ original_line_index = 0
    while original_line_index < len(original_lines):
        if original_line_index in original_background_events:
            $ original_current_background = original_background_events[original_line_index]
            scene expression original_current_background at original_center_4_3
            with dissolve
            $ original_gallery_record_image(original_current_background)
        if original_line_index in original_choice_events:
            $ original_choice_event = original_choice_events[original_line_index]
            $ original_choice_items = [("[original_linear_choice_text(%d)]" % index, index) for index, option in enumerate(original_choice_event["options"])]
            $ original_choice_result = renpy.display_menu(original_choice_items)
            $ original_choice_text = original_linear_choice_text(original_choice_result)
            $ original_choice_history = original_choice_history + [(original_line_index, original_choice_result, original_choice_text)]
            $ original_line_index += original_choice_event["skip_lines"]
        else:
            $ original_current_line = original_localize_script_line(ORIGINAL_SCRIPT_FILE, original_line_index, original_lines[original_line_index])
            if original_current_line:
                $ original_dialogue_context = ("file", ORIGINAL_SCRIPT_FILE, original_line_index, original_lines[original_line_index])
                call expression original_dialogue_label()
                $ original_dialogue_context = None
            $ original_line_index += 1

    "纯脚本已经播放完毕。"
    jump original_hub

label original_scenario_file_reader:
    $ original_scenario_events = original_load_scenario_events(original_scenario_name)
    $ original_scenario_route = original_load_scenario_route(original_scenario_name)
    $ original_scenario_state = original_scenario_route_begin(original_scenario_events, original_scenario_route)
    $ original_scenario_last_choice = None
    $ original_scenario_aux_stage = original_auxiliary_progress.get(original_scenario_name, 0)

    $ original_scenario_group = original_scenario_route_next(original_scenario_state)
    while original_scenario_group is not None:
        $ original_scenario_group_choice = None
        $ original_scenario_event_index = 0
        while original_scenario_event_index < len(original_scenario_group["events"]):
            $ original_scenario_event = original_scenario_group["events"][original_scenario_event_index]
            $ original_scenario_event_index += 1
            if original_scenario_event["type"] == "audio":
                $ original_audio_execute(original_scenario_event)
            elif original_scenario_event["type"] == "control":
                $ original_presentation_execute(original_scenario_event)
            elif original_scenario_event["type"] == "background":
                $ original_current_background = original_scenario_event["image"]
                scene expression original_current_background at original_center_4_3
                if original_scenario_event.get("transition", True):
                    with dissolve
                $ original_gallery_record_image(original_current_background)
            elif original_scenario_event["type"] == "choice":
                $ original_scenario_options = original_localize_event(original_scenario_event)
                $ original_scenario_items = [("[original_scenario_choice_label(%d)]" % index, index) for index in original_scenario_choice_indices(original_scenario_event)]
                $ original_scenario_group_choice = renpy.display_menu(original_scenario_items)
                $ original_scenario_last_choice = original_scenario_group_choice
                $ original_scenario_choice_text = original_localize_event(original_scenario_event)[original_scenario_group_choice]
                $ original_choice_history = original_choice_history + [(original_scenario_event["id"], original_scenario_group_choice, original_scenario_choice_text)]
            elif original_scenario_event["type"] == "call":
                if "stage" not in original_scenario_event or original_scenario_event["stage"] == original_scenario_aux_stage:
                    $ original_scenario_push_call()
                    $ original_scenario_name = original_scenario_event["scenario"]
                    call original_scenario_file_reader
                    $ original_scenario_pop_call(_return)
            elif original_scenario_event["type"] == "jump":
                $ original_scenario_route_jump(original_scenario_state, original_scenario_event["target"])
            elif original_scenario_event["type"] == "branch":
                if original_scenario_last_choice != original_scenario_event["value"]:
                    $ original_scenario_route_jump(original_scenario_state, original_scenario_event["target"])
            elif original_scenario_event["type"] == "text":
                $ original_scenario_text = original_localize_event(original_scenario_event)
                if original_scenario_text and original_scenario_event.get("dialogue_group", original_scenario_event["id"]) == original_scenario_event["id"]:
                    $ original_dialogue_context = ("event", original_scenario_event)
                    call expression original_dialogue_label()
                    $ original_dialogue_context = None

        $ original_scenario_route_apply_choice(original_scenario_state, original_scenario_group_choice)
        $ original_scenario_group = original_scenario_route_next(original_scenario_state)

    if any(event.get("type") == "text" for event in original_scenario_events):
        $ original_gallery_complete_scenario(original_scenario_name)
    $ original_supplemental_finish(original_scenario_name)
    return original_scenario_last_choice

label original_cg_gallery:
    $ ShowMenu("original_cg_gallery_ui")()
    return

label original_sound_test:
    $ ShowMenu("original_sound_gallery_ui")()
    return

label original_scene_gallery:
    $ ShowMenu("original_scene_gallery_ui")()
    return

label original_scene_reader:
    if not original_gallery_unlocked("scene", original_selected_scene):
        return
    $ original_audio_stop()
    $ original_gallery_replay_mode = True
    $ original_scenario_name = ORIGINAL_SCENE_UNLOCK_GROUPS[original_selected_scene][0][0]
    call original_scenario_file_reader
    $ original_gallery_replay_mode = False
    return

label original_movie_gallery:
    $ ShowMenu("original_ending_gallery_ui")()
    return

label original_ending_reader:
    if not original_gallery_unlocked("ending", original_selected_ending):
        return
    $ original_audio_stop()
    $ original_gallery_replay_mode = True
    $ original_scenario_name = ORIGINAL_ENDING_UNLOCK_SCENARIOS[original_selected_ending]
    call original_scenario_file_reader
    $ original_gallery_replay_mode = False
    call original_story_video(original_ending_movie_path(original_selected_ending))
    return
