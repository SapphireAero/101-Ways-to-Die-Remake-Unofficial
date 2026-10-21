# Public source edition: the runtime uses only the authored demonstration data.
default original_dialogue_context = None

init python:
    ORIGINAL_DATA_DIRECTORY = "demo/data"
    ORIGINAL_SCRIPT_FILE = ORIGINAL_DATA_DIRECTORY + "/pure_script.txt"
    ORIGINAL_BACKGROUND_EVENTS_FILE = ORIGINAL_DATA_DIRECTORY + "/background_events.json"
    ORIGINAL_CHOICE_EVENTS_FILE = ORIGINAL_DATA_DIRECTORY + "/choice_events.json"
    ORIGINAL_SCENARIO_EVENTS_FILE = ORIGINAL_DATA_DIRECTORY + "/scenario_events.json"
    ORIGINAL_SCENARIO_ROUTE_FILE = ORIGINAL_DATA_DIRECTORY + "/scenario_routes.json"
    ORIGINAL_ROUTE_FILE = ORIGINAL_DATA_DIRECTORY + "/route_flow_draft.json"
    ORIGINAL_SCENARIO_TRANSLATION_DIR = ORIGINAL_DATA_DIRECTORY + "/translations"
    PUBLIC_CATALOG = __import__("json").loads(renpy.file(ORIGINAL_DATA_DIRECTORY + "/catalog.json").read().decode("utf-8"))
    ORIGINAL_CG = [tuple(entry) for entry in PUBLIC_CATALOG["cg"]]
    ORIGINAL_SOUNDS = []
    ORIGINAL_MOVIES = []
    _original_dict_type = __import__("builtins").dict
    _original_list_type = __import__("builtins").list
    _original_scenario_source = None
    _original_scenario_cache = {}
    _original_text_translation_cache = {}
    _original_translation_tables = {}
    _original_scenario_route_source = None
    _original_route_source = None

    def original_load_script_lines():
        try:
            raw = renpy.file(ORIGINAL_SCRIPT_FILE).read()
        except Exception:
            return []
        if isinstance(raw, bytes):
            text = raw.decode("utf-8-sig", "replace")
        else:
            text = raw
        return [line.strip() for line in text.splitlines() if line.strip()]

    def original_load_background_events():
        try:
            raw = renpy.file(ORIGINAL_BACKGROUND_EVENTS_FILE).read()
        except Exception:
            return {}
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8-sig", "replace")
        try:
            source_events = __import__("json").loads(raw)
        except Exception:
            return {}

        events = {}
        for event in source_events:
            try:
                line_index = int(event["line"])
                image_path = event["image"]
            except (KeyError, TypeError, ValueError):
                continue
            if renpy.loadable(image_path):
                events[line_index] = image_path
        return events

    def original_load_choice_events():
        try:
            raw = renpy.file(ORIGINAL_CHOICE_EVENTS_FILE).read()
        except Exception:
            return {}
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8-sig", "replace")
        try:
            source_events = __import__("json").loads(raw)
        except Exception:
            return {}

        events = {}
        for event in source_events:
            try:
                line_index = int(event["line"])
                options = [str(option) for option in event["options"]]
                skip_lines = int(event["skip_lines"])
            except (KeyError, TypeError, ValueError):
                continue
            if options and skip_lines > 0:
                events[line_index] = {
                    "options": options,
                    "skip_lines": skip_lines,
                    "source": event.get("source", ""),
                }
        return events

    def original_load_scenario_events(scenario_name):
        global _original_scenario_source

        scenario_name = str(scenario_name).upper()
        language = getattr(renpy.game.preferences, "language", None)
        if language:
            language = str(language)
            if not __import__("re").fullmatch(r"[A-Za-z0-9_-]+", language):
                language = None

        # Ren'Py uses None for the game's default language. The JSON reader
        # uses an explicit file name so the default Chinese route can be added
        # without changing Ren'Py's source language semantics.
        translation_language = language or "schinese"
        cache_key = (scenario_name, translation_language)
        if cache_key in _original_scenario_cache:
            return _original_scenario_cache[cache_key]

        if _original_scenario_source is None:
            try:
                raw = renpy.file(ORIGINAL_SCENARIO_EVENTS_FILE).read()
                if isinstance(raw, bytes):
                    raw = raw.decode("utf-8-sig", "replace")
                _original_scenario_source = __import__("json").loads(raw)
            except Exception:
                _original_scenario_source = {}
            if not isinstance(_original_scenario_source, _original_dict_type):
                _original_scenario_source = {}

        # Keep route state in source language. Translating this snapshot would
        # leave already queued events in the previous language after switching.
        events = []
        for source_event in _original_scenario_source.get(scenario_name, []):
            if not isinstance(source_event, _original_dict_type):
                continue
            event = dict(source_event)
            events.append(event)

        events = original_audio_events(scenario_name, events)
        _original_scenario_cache[cache_key] = events
        return events

    def original_translation_language():
        """Return the JSON language key used by the dynamic text reader."""
        language = getattr(renpy.game.preferences, "language", None)
        if language:
            language = str(language)
            if not __import__("re").fullmatch(r"[A-Za-z0-9_-]+", language):
                language = None
        return language or "schinese"

    def original_load_translation_table(language=None):
        """Load the optional text map shared by script and gallery readers."""
        language = language or original_translation_language()
        if language in _original_translation_tables:
            return _original_translation_tables[language]
        table = {}
        try:
            translation_file = "%s/%s.json" % (
                ORIGINAL_SCENARIO_TRANSLATION_DIR,
                language,
            )
            raw = renpy.file(translation_file).read()
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8-sig", "replace")
            table = __import__("json").loads(raw)
        except Exception:
            table = {}

        table = table if hasattr(table, "get") else {}
        _original_translation_tables[language] = table
        return table

    def original_localize_event(event):
        """Resolve an event at display time, including after a language change."""
        field = "options" if event.get("type") == "choice" else "text"
        source = event.get(field, [] if field == "options" else "")
        # Old saves can contain a translated event snapshot. Recover the source
        # by its stable ID before applying the currently selected language.
        event_id = event.get("id", "")
        if event_id:
            name = event_id.split(":", 1)[0]
            for candidate in original_load_scenario_events(name):
                if candidate.get("id") == event_id:
                    source = candidate.get(field, source)
                    break
        replacement = original_load_translation_table().get(event_id)
        if replacement is None:
            return source
        if field == "options":
            if isinstance(replacement, _original_list_type) and len(replacement) == len(source):
                return replacement
            return source
        return replacement if hasattr(replacement, "strip") else source

    def original_scenario_display_text():
        return original_escape_text(original_localize_event(original_scenario_event))

    def original_scenario_choice_label(index):
        return original_escape_text(original_localize_event(original_scenario_event)[index])

    def original_localize_script_line(filename, index, source):
        """Use a file/line key so repeated names and lines cannot collide."""
        files = original_load_translation_table().get("files", {})
        lines = files.get(filename, []) if hasattr(files, "get") else []
        if 0 <= index < len(lines):
            return lines[index]
        return original_localize_text(source)

    def original_script_display_text(filename, index, lines):
        return original_escape_text(original_localize_script_line(filename, index, lines[index]))

    def original_context_text(context, fallback):
        if not context:
            return fallback
        if context[0] == "event":
            return original_escape_text(original_localize_event(context[1]))
        if context[0] == "file":
            return original_escape_text(original_localize_script_line(context[1], context[2], context[3]))
        return fallback

    def original_dialogue_display_text(what):
        # Character interpolation runs once before interaction. Resolve again
        # in the say screen so preferences can update the currently visible line.
        return original_context_text(original_dialogue_context, what)

    def original_record_dialogue_source(entry):
        if original_dialogue_context:
            entry.original_source_context = original_dialogue_context

    def original_history_text(entry):
        return original_context_text(getattr(entry, "original_source_context", None), entry.what)

    config.history_callbacks.append(original_record_dialogue_source)

    def original_linear_choice_text(index):
        choice = original_choice_event
        source = choice.get("source", "")
        translations = original_load_translation_table()
        choices = translations.get("choices", {})
        options = choices.get(source, choice["options"])
        if len(options) != len(choice["options"]):
            options = choice["options"]
        return original_escape_text(options[index])

    def original_localize_text(text):
        """Translate a line or choice by source text when an ID is unavailable."""
        if text is None:
            return text

        language = original_translation_language()
        cache_key = (language, text)
        if cache_key in _original_text_translation_cache:
            return _original_text_translation_cache[cache_key]

        table = original_load_translation_table(language)
        text_table = table.get("text", {})
        replacement = text_table.get(text) if hasattr(text_table, "get") else None
        if replacement is None:
            # Also accept a flat source-text map for compatibility with older
            # translation files.
            replacement = table.get(text)
        if replacement is None:
            replacement = text

        _original_text_translation_cache[cache_key] = replacement
        return replacement

    def original_load_scenario_route(scenario_name):
        """Load the optional branch ranges embedded in one scenario file."""
        global _original_scenario_route_source

        if _original_scenario_route_source is None:
            try:
                raw = renpy.file(ORIGINAL_SCENARIO_ROUTE_FILE).read()
                if isinstance(raw, bytes):
                    raw = raw.decode("utf-8-sig", "replace")
                source = __import__("json").loads(raw)
            except Exception:
                source = {}
            _original_scenario_route_source = source if isinstance(source, _original_dict_type) else {}

        item = _original_scenario_route_source.get(str(scenario_name).upper(), {})
        if not isinstance(item, _original_dict_type):
            return {"conditions": {}}

        conditions = {}
        for condition in item.get("conditions", []):
            if not isinstance(condition, _original_dict_type):
                continue
            try:
                choice_offset = int(condition["choice_offset"])
                option_count = int(condition["option_count"])
                group_end = int(condition["group_end"])
            except (KeyError, TypeError, ValueError):
                continue
            branches = []
            for branch in condition.get("branches", []):
                try:
                    start = int(branch["start"])
                    end = int(branch["end"])
                except (KeyError, TypeError, ValueError):
                    continue
                if end > start:
                    branches.append({"start": start, "end": end})
            if option_count > 0 and len(branches) == option_count:
                conditions[choice_offset] = {
                    "option_count": option_count,
                    "group_end": group_end,
                    "branches": branches,
                }
        return {"conditions": conditions}

    def original_scenario_route_begin(events, route):
        """Build a serializable event-group interpreter for one scenario."""
        groups = []
        by_offset = {}
        for event in events or []:
            try:
                offset = int(str(event.get("offset", "0")), 16)
            except (AttributeError, TypeError, ValueError):
                continue
            group = by_offset.get(offset)
            if group is None:
                group = {"offset": offset, "events": []}
                by_offset[offset] = group
                groups.append(group)
            group["events"].append(event)
        groups.sort(key=lambda item: item["offset"])
        if not groups:
            return {"groups": [], "conditions": {}, "frames": [], "pending": None, "done": True}

        ceiling = groups[-1]["offset"] + 1
        return {
            "groups": groups,
            "conditions": (route or {}).get("conditions", {}),
            "frames": [{
                "cursor": groups[0]["offset"],
                "end": ceiling,
                "ceiling": ceiling,
            }],
            "pending": None,
            "done": False,
        }

    def original_scenario_route_next(state):
        """Return the next event group and pause at a branch choice."""
        if not isinstance(state, _original_dict_type) or state.get("done"):
            return None
        if state.get("pending") is not None:
            return state["pending"]

        groups = state.get("groups", [])
        frames = state.get("frames", [])
        while frames:
            frame = frames[-1]
            cursor = int(frame.get("cursor", 0))
            end = int(frame.get("end", 0))
            candidate = None
            for group in groups:
                offset = int(group["offset"])
                if offset >= cursor and offset < end:
                    candidate = group
                    break
            if candidate is None:
                frames.pop()
                continue

            frame["cursor"] = int(candidate["offset"]) + 1
            pending = {
                "offset": int(candidate["offset"]),
                "events": candidate["events"],
            }
            state["pending"] = pending
            return pending

        state["done"] = True
        return None

    def original_scenario_route_apply_choice(state, result):
        """Select one scenario branch and resume its shared continuation."""
        if not isinstance(state, _original_dict_type):
            return
        pending = state.get("pending")
        state["pending"] = None
        if not pending:
            return

        node = state.get("conditions", {}).get(int(pending["offset"]))
        if node is None:
            return
        try:
            option = int(result)
        except (TypeError, ValueError):
            option = 0
        option = max(0, min(option, int(node["option_count"]) - 1))
        branches = node.get("branches", [])
        if option >= len(branches):
            return

        frames = state.get("frames", [])
        if not frames:
            state["done"] = True
            return
        parent = frames[-1]
        group_end = int(node["group_end"])
        parent["cursor"] = group_end
        if group_end > int(parent.get("end", 0)):
            parent["end"] = int(parent.get("ceiling", group_end))
        branch = branches[option]
        frames.append({
            "cursor": int(branch["start"]),
            "end": int(branch["end"]),
            "ceiling": group_end,
        })

    def original_load_route_data():
        """Load the route table generated from ScenarioRoot.FOB.

        The route file contains bytecode offsets rather than Ren'Py labels. The
        reader uses those offsets to preserve nested branches and shared
        continuation segments from the original game.
        """
        global _original_route_source

        if _original_route_source is not None:
            return _original_route_source

        try:
            raw = renpy.file(ORIGINAL_ROUTE_FILE).read()
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8-sig", "replace")
            source = __import__("json").loads(raw)
        except Exception:
            source = {}

        if not isinstance(source, _original_dict_type):
            source = {}

        calls = []
        for item in source.get("scenario_calls", []):
            if not isinstance(item, _original_dict_type):
                continue
            try:
                offset = int(item["offset"])
                scenario = str(item["scenario"]).upper()
            except (KeyError, TypeError, ValueError):
                continue
            calls.append({"offset": offset, "scenario": scenario})
        calls.sort(key=lambda item: item["offset"])

        conditions = {}
        for item in source.get("conditions", []):
            if not isinstance(item, _original_dict_type):
                continue
            try:
                call_offset = int(str(item["source_call_offset"]), 16)
                option_count = int(item["option_count"])
                group = item["branch_group"]
                group_end = int(str(group["metadata_end"]), 16)
            except (KeyError, TypeError, ValueError):
                continue
            branches = []
            for branch in item.get("branches", []):
                try:
                    start = int(str(branch["range"][0]), 16)
                    end = int(str(branch["range"][1]), 16)
                except (KeyError, IndexError, TypeError, ValueError):
                    continue
                branches.append({"start": start, "end": end})
            if branches and option_count > 0:
                conditions[call_offset] = {
                    "option_count": option_count,
                    "group_end": group_end,
                    "branches": branches,
                }

        root_end = source.get("root_end")
        try:
            root_end = int(root_end)
        except (TypeError, ValueError):
            root_end = (calls[-1]["offset"] + 1) if calls else 0

        _original_route_source = {
            "calls": calls,
            "conditions": conditions,
            "root_end": root_end,
        }
        return _original_route_source

    def original_route_begin():
        """Create a serializable interpreter state for the original route."""
        route = original_load_route_data()
        calls = route["calls"]
        if not calls:
            return {"calls": [], "conditions": {}, "frames": [], "pending": None, "done": True}

        return {
            "calls": calls,
            "conditions": route["conditions"],
            "frames": [{
                "cursor": calls[0]["offset"],
                "end": route["root_end"],
                "ceiling": route["root_end"],
            }],
            "pending": None,
            "done": False,
        }

    def original_route_next(state):
        """Return the next scenario call and pause until its choice is known."""
        if not isinstance(state, _original_dict_type) or state.get("done"):
            return None
        if state.get("pending") is not None:
            return state["pending"]

        calls = state.get("calls", [])
        frames = state.get("frames", [])
        while frames:
            frame = frames[-1]
            cursor = int(frame.get("cursor", 0))
            end = int(frame.get("end", 0))
            candidate = None
            for item in calls:
                offset = int(item["offset"])
                if offset >= cursor and offset < end:
                    candidate = item
                    break
            if candidate is None:
                frames.pop()
                continue

            frame["cursor"] = int(candidate["offset"]) + 1
            pending = {
                "offset": int(candidate["offset"]),
                "scenario": str(candidate["scenario"]).upper(),
            }
            state["pending"] = pending
            return pending

        state["done"] = True
        return None

    def original_route_apply_choice(state, result):
        """Apply a choice and push the matching bytecode branch interval."""
        if not isinstance(state, _original_dict_type):
            return
        pending = state.get("pending")
        state["pending"] = None
        if not pending:
            return

        node = state.get("conditions", {}).get(int(pending["offset"]))
        if node is None:
            return

        try:
            option = int(result)
        except (TypeError, ValueError):
            option = 0
        option = max(0, min(option, int(node["option_count"]) - 1))
        branches = node.get("branches", [])
        if option >= len(branches):
            return

        frames = state.get("frames", [])
        if not frames:
            state["done"] = True
            return

        parent = frames[-1]
        group_end = int(node["group_end"])
        parent["cursor"] = group_end
        # A nested branch can jump past its lexical range into a shared
        # continuation. Extend only that active branch frame to its ceiling.
        if group_end > int(parent.get("end", 0)):
            parent["end"] = int(parent.get("ceiling", group_end))

        branch = branches[option]
        frames.append({
            "cursor": int(branch["start"]),
            "end": int(branch["end"]),
            "ceiling": group_end,
        })

    def original_escape_text(text):
        return str(text).replace("{", "{{")
