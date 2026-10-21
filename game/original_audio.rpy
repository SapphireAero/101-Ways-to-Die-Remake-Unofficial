# Audio recovered from the original FOB bytecode and TextFunc inline controls.
init -1 python:
    for _original_se_index in range(3):
        renpy.music.register_channel("original_se_%d" % _original_se_index, mixer="sfx", loop=False)
    renpy.music.register_channel("original_music_preview", mixer="music", loop=True)
    config.main_menu_stop_channels.extend(["original_se_%d" % index for index in range(3)] + ["original_music_preview"])

init 1 python:
    ORIGINAL_BGM = {int(key): value for key, value in PUBLIC_CATALOG.get("bgm", {}).items()}
    ORIGINAL_SE = {int(key): value for key, value in PUBLIC_CATALOG.get("se", {}).items()}
    _original_audio_source = None

    def original_audio_events(scenario_name, events):
        global _original_audio_source
        if _original_audio_source is None:
            _original_audio_source = __import__("json").loads(
                renpy.file(ORIGINAL_DATA_DIRECTORY + "/scenario_audio.json").read().decode("utf-8-sig"))
        return original_story_merge_events(scenario_name, events, _original_audio_source)

    def original_audio_wait(channel):
        # Waiting is click/skip interruptible, as in TextFunc. Give the decoder
        # an interaction to open the new WAV, then stop the SE after waiting.
        duration, position = 0.0, None
        for attempt in range(10):
            if renpy.pause(0.02):
                renpy.music.stop(channel=channel, fadeout=0)
                return
            duration = renpy.music.get_duration(channel=channel)
            position = renpy.music.get_pos(channel=channel)
            if duration and position is not None:
                break
        if duration and position is not None:
            renpy.pause(max(0.0, duration - position))
        renpy.music.stop(channel=channel, fadeout=0)

    def original_audio_execute(event):
        command = event["command"]
        if command == "PlayCD":
            track = event["track"]
            # Track 13 is the original CD's short silent stop track.
            if track == 13:
                renpy.music.stop(channel="music", fadeout=0)
            else:
                renpy.music.play(ORIGINAL_BGM[track], channel="music",
                                 loop=event["loop"], if_changed=True, fadeout=0)
        elif command in ("StopCD", "StopCD2"):
            renpy.music.stop(channel="music", fadeout=0)
        elif command == "SeStopAll":
            for index in range(3):
                renpy.music.stop(channel="original_se_%d" % index, fadeout=0)
        else:
            channel = "original_se_%d" % event["channel"]
            if command in ("SePlay", "SePlayEx"):
                renpy.music.play(ORIGINAL_SE[event["sound"]], channel=channel,
                                 loop=event["loop"], fadeout=0)
                if command == "SePlayEx":
                    original_audio_wait(channel)
            elif command == "SeWait":
                original_audio_wait(channel)
            elif command in ("SeStop", "SeStopFade"):
                renpy.music.stop(channel=channel, fadeout=1.0 if command == "SeStopFade" else 0)

    def original_audio_stop():
        renpy.music.stop(channel="music", fadeout=0)
        original_audio_execute({"command": "SeStopAll"})

    def original_music_preview_begin():
        renpy.music.set_pause(True, channel="music")

    def original_music_preview_end():
        renpy.music.stop(channel="original_music_preview", fadeout=0)
        renpy.music.set_pause(False, channel="music")

    def original_audio_upgrade_frame(frame):
        """Keep the consumed event boundary, even when its group was removed."""
        normalized = original_scenario_normalize_frame(frame)
        state = frame.get("original_scenario_state")
        if not state or not state.get("groups"):
            return normalized
        current = frame.get("original_scenario_group") or state.get("pending")
        if current is not None:
            frame["original_scenario_group"] = current
            old_index = frame.get("original_scenario_event_index")
            if not isinstance(old_index, int) or isinstance(old_index, bool):
                current_id = (frame.get("original_scenario_event") or {}).get("id")
                index = next((position + 1 for position, event in enumerate(current["events"])
                              if event["id"] == current_id), 0)
            else:
                index = max(0, min(old_index, len(current["events"])))
            normalized = normalized or old_index != index or type(old_index) is not int
            frame["original_scenario_event_index"] = index
        events = original_load_scenario_events(frame["original_scenario_name"])
        def signature(event):
            return (event["id"], event.get("dialogue_group"), event.get("dialogue_key"))
        old_ids = [signature(event) for group in state["groups"] for event in group["events"]]
        if old_ids == [signature(event) for event in events]:
            return normalized
        updated = original_scenario_route_begin(events, frame["original_scenario_route"])
        old_ceiling = state["groups"][-1]["offset"] + 1
        new_ceiling = updated["groups"][-1]["offset"] + 1 if updated["groups"] else old_ceiling
        for branch in state["frames"]:
            for key in ("end", "ceiling"):
                if branch[key] == old_ceiling:
                    branch[key] = new_ceiling
        state["groups"] = updated["groups"]
        if current:
            old_events = current["events"]
            consumed = {event["id"] for event in old_events[:index]}
            group = next((group for group in state["groups"]
                          if group["offset"] == current["offset"]), None)
            # Keep a removed group as an empty pending group. Its existing
            # cursor then visits the replacement at its real bytecode offset,
            # rather than guessing an offset or skipping the following text.
            current["events"] = group["events"] if group else []
            frame["original_scenario_event_index"] = max(
                (position + 1 for position, event in enumerate(current["events"])
                 if event["id"] in consumed), default=0)
            pending = state.get("pending")
            if pending is not None and pending["offset"] == current["offset"]:
                state["pending"] = current
        frame["original_scenario_events"] = events
        return True

    def original_story_frame_state(frame, inherited=None):
        """Recover state on the saved path without playing past interactions."""
        active = dict(inherited or {})
        choices = {item[0]: item[1] for item in original_choice_history}
        current = frame.get("original_scenario_group")
        if not current:
            return active
        boundary = (current["offset"], frame.get("original_scenario_event_index") or 0)

        def visit(name, events, route, stage, stop=None, parents=()):
            if name in parents:
                return None
            state = original_scenario_route_begin(events, route)
            last_choice = None
            group = original_scenario_route_next(state)
            while group is not None:
                if stop is not None and group["offset"] > stop[0]:
                    return last_choice
                result = None
                for index, event in enumerate(group["events"]):
                    at_boundary = stop is not None and group["offset"] == stop[0]
                    if at_boundary and index >= stop[1]:
                        return last_choice
                    kind = event["type"]
                    if kind == "audio":
                        command = event["command"]
                        if command in ("PlayCD", "StopCD", "StopCD2"):
                            active["music"] = event
                        elif command == "SeStopAll":
                            for channel in range(3):
                                active[channel] = {"type": "audio", "command": "SeStop", "channel": channel}
                        elif command in ("SePlay", "SePlayEx", "SeStop", "SeStopFade", "SeWait"):
                            channel = event["channel"]
                            active[channel] = event if command == "SePlay" and event["loop"] else {
                                "type": "audio", "command": "SeStop", "channel": channel}
                    elif kind == "background":
                        active["background"] = event
                    elif kind == "control" and event["command"] not in ("WaitTime", "WaitKey"):
                        active["window"] = event
                    elif kind == "choice":
                        result = last_choice = choices.get(event["id"], 0)
                    elif kind == "call":
                        # A parent frame stops inside the call to the active
                        # child. That child's own saved prefix is restored next.
                        if at_boundary and index + 1 == stop[1]:
                            return last_choice
                        if "stage" not in event or event["stage"] == stage:
                            child = event["scenario"]
                            value = visit(child, original_load_scenario_events(child),
                                          original_load_scenario_route(child), 0,
                                          parents=parents + (name,))
                            if value is not None:
                                result = last_choice = value
                    elif kind == "jump" or (kind == "branch" and last_choice != event["value"]):
                        original_scenario_route_jump(state, event["target"])
                if stop is not None and group["offset"] == stop[0]:
                    return last_choice
                original_scenario_route_apply_choice(state, result)
                group = original_scenario_route_next(state)
            return last_choice

        visit(frame["original_scenario_name"], frame["original_scenario_events"],
              frame["original_scenario_route"], frame.get("original_scenario_aux_stage") or 0, boundary)
        return active

    def original_audio_before_event(frame):
        return [event for event in original_story_frame_state(frame).values() if event["type"] == "audio"]

    def original_audio_after_load():
        fields = _original_scenario_frame_fields
        frame = {name: getattr(store, name, None) for name in fields}
        context = getattr(store, "original_dialogue_context", None)
        if frame.get("original_scenario_event") is None and context and context[0] == "event":
            frame["original_scenario_event"] = context[1]
        parents = getattr(store, "original_scenario_call_stack", ()) or ()
        candidates = list(parents) + [frame]
        upgraded = [original_audio_upgrade_frame(candidate) for candidate in candidates]
        if any(upgraded):
            active = {}
            for candidate in candidates:
                if candidate.get("original_scenario_state"):
                    active = original_story_frame_state(candidate, active)
            for event in active.values():
                if event["type"] == "audio":
                    original_audio_execute(event)
            background = active.get("background")
            if background is not None:
                store.original_current_background = background["image"]
                renpy.scene()
                renpy.show(background["image"], at_list=[original_center_4_3])
                original_gallery_record_image(background["image"])
            if "window" in active:
                original_presentation_execute(active["window"], restoring=True)
        for name, value in frame.items():
            if value is not None:
                setattr(store, name, value)
        if any(upgraded):
            # Rolling back across this boundary would restore the old queue.
            renpy.block_rollback()

    config.after_load_callbacks.append(original_audio_after_load)
