# Source visual cues are merged with audio and text before branch dispatch.
init python:
    _original_visual_source = None
    _original_control_source = None
    _original_dialogue_source = None

    def original_story_align_events(scenario_name, events):
        global _original_dialogue_source
        if _original_dialogue_source is None:
            _original_dialogue_source = __import__("json").loads(
                renpy.file(ORIGINAL_DATA_DIRECTORY + "/scenario_dialogue.json").read().decode("utf-8-sig"))
        by_id = {event["id"]: event for event in events if event["type"] == "text"}
        for paragraph in _original_dialogue_source.get(str(scenario_name).upper(), ()):
            first = paragraph["ids"][0]
            for event_id in paragraph["ids"]:
                event = by_id.get(event_id)
                if event is not None:
                    event["text"] = paragraph["text"]
                    event["dialogue_group"] = first
                    # New combined paragraphs must not inherit a read marker
                    # from just the first physical line of an older version.
                    if len(paragraph["ids"]) > 1:
                        event["dialogue_key"] = first + ":paragraph:1"
        return events

    def original_story_merge_events(scenario_name, events, audio):
        global _original_visual_source, _original_control_source
        if _original_visual_source is None:
            _original_visual_source = __import__("json").loads(
                renpy.file(ORIGINAL_DATA_DIRECTORY + "/scenario_visual.json").read().decode("utf-8-sig"))
        if _original_control_source is None:
            _original_control_source = __import__("json").loads(
                renpy.file(ORIGINAL_DATA_DIRECTORY + "/scenario_control.json").read().decode("utf-8-sig"))
        name = str(scenario_name).upper()
        events = original_story_align_events(name, events)
        visuals = _original_visual_source.get(name)
        if visuals is not None:
            events = [event for event in events if event["type"] != "background"]
        before, after, direct = {}, {}, []
        for item in list(visuals or ()) + list(audio.get(name, ())) + list(_original_control_source.get(name, ())):
            if "anchor" in item:
                target = after if item["position"] == "after" else before
                target.setdefault(item["anchor"], []).append(item)
            else:
                direct.append(item)
        for target in (before, after):
            for items in target.values():
                items.sort(key=lambda item: item.get("control_index", -1))
        merged = []
        for event in events:
            merged.extend(before.get(event["id"], ()))
            merged.append(event)
            merged.extend(after.get(event["id"], ()))
        merged.extend(direct)
        merged.sort(key=lambda event: int(event["offset"], 16))
        return merged

    def original_dialogue_label():
        context = original_dialogue_context
        key = context[1].get("dialogue_key", context[1]["id"]) if context[0] == "event" else "file:%s:%d" % (context[1], context[2])
        return "original_line_" + __import__("hashlib").sha256(key.encode("utf-8")).hexdigest()[:24]

    def original_dynamic_text():
        return original_context_text(original_dialogue_context, "")

    def original_dialogue_window_height(what):
        # A patch page can combine several source paragraphs. Grow the text
        # panel for those pages while keeping the regular layout for short ones.
        text = original_dialogue_display_text(what)
        east_asian_width = __import__("unicodedata").east_asian_width
        columns = max(1, gui.dialogue_width / float(gui.text_size))
        rows = sum(max(1, __import__("math").ceil(
            sum(1.0 if east_asian_width(char) in ("W", "F", "A") else 0.6 for char in line) / columns))
            for line in text.split("\n"))
        return min(config.screen_height - 100,
                   max(gui.textbox_height, int(gui.dialogue_ypos + rows * (gui.text_size * 1.4) + 30)))

    def original_opening_movie_path():
        return PUBLIC_CATALOG.get("opening_movie", "")

label original_story_video(path):
    if renpy.loadable(path):
        window hide
        $ original_audio_stop()
        $ renpy.movie_cutscene(path)
    return
