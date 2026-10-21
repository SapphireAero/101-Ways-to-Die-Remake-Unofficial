# Per-playthrough dispatch flags. Gallery completion remains in persistent.
default original_auxiliary_progress = {}
default original_scenario_call_stack = []
default original_scenario_aux_stage = None
default original_gallery_replay_mode = False

init python:
    _original_scenario_frame_fields = (
        "original_scenario_name", "original_scenario_events", "original_scenario_route",
        "original_scenario_state", "original_scenario_last_choice", "original_scenario_group",
        "original_scenario_group_choice", "original_scenario_event_index", "original_scenario_event",
        "original_scenario_aux_stage",
    )

    def original_scenario_normalize_frame(frame):
        """Supply fields added after the earliest scenario-reader saves."""
        if not frame.get("original_scenario_name"):
            return False
        stage = frame.get("original_scenario_aux_stage")
        if isinstance(stage, int) and not isinstance(stage, bool) and stage >= 0:
            return False
        progress = getattr(renpy.store, "original_auxiliary_progress", None) or {}
        stage = progress.get(frame["original_scenario_name"], 0)
        frame["original_scenario_aux_stage"] = stage if isinstance(stage, int) and not isinstance(stage, bool) and stage >= 0 else 0
        return True

    def original_scenario_push_call():
        frame = {name: getattr(renpy.store, name, None) for name in _original_scenario_frame_fields}
        original_scenario_normalize_frame(frame)
        renpy.store.original_scenario_aux_stage = frame["original_scenario_aux_stage"]
        original_scenario_call_stack.append(frame)

    def original_scenario_pop_call(result):
        frame = original_scenario_call_stack.pop()
        original_scenario_normalize_frame(frame)
        for name, value in frame.items():
            setattr(renpy.store, name, value)
        # GetLastTxtID in the source observes a menu inside a child script.
        # A child without a menu leaves its parent's last result unchanged.
        if result is not None:
            renpy.store.original_scenario_last_choice = result
            renpy.store.original_scenario_group_choice = result

    def original_scenario_route_jump(state, target):
        ceiling = max(frame["ceiling"] for frame in state["frames"])
        state["frames"] = [{"cursor": target, "end": ceiling, "ceiling": ceiling}]
        state["pending"] = None

    def original_supplemental_finish(name):
        if original_gallery_replay_mode:
            return
        limit = PUBLIC_CATALOG.get("auxiliary_limits", {}).get(name)
        if limit is not None:
            original_auxiliary_progress[name] = min(original_auxiliary_progress.get(name, 0) + 1, limit)

    def original_scenario_choice_indices(event):
        return list(range(len(event.get("options", ()))))
