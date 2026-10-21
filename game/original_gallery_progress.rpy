# Gallery progress belongs to the player, not to an individual save or language.
default persistent.original_completed_scenarios = set()

init 1 python:
    # Each slot follows the source FOB files used to build its replay. Inner
    # tuples are alternatives (G2 has two mutually exclusive responses).
    ORIGINAL_SCENE_UNLOCK_GROUPS = tuple(((entry["scenario"],),) for entry in PUBLIC_CATALOG["scenes"])
    ORIGINAL_ENDING_UNLOCK_SCENARIOS = tuple(entry["scenario"] for entry in PUBLIC_CATALOG["endings"])
    _original_gallery_cg_by_path = {entry[1]: entry[0] for entry in ORIGINAL_GALLERY_CG}

    def original_gallery_merge_progress(old, new, current):
        return set(old or ()) | set(new or ()) | set(current or ())

    renpy.register_persistent("original_completed_scenarios", original_gallery_merge_progress)

    def original_gallery_completed():
        return set(persistent.original_completed_scenarios or ())

    def original_gallery_record_image(path):
        """Call only when the story displays a CG, never when drawing its album."""
        if getattr(renpy.store, "original_gallery_replay_mode", False) or _in_replay:
            return
        if path in _original_gallery_cg_by_path and not renpy.seen_image(path):
            renpy.mark_image_seen(path)
            renpy.save_persistent()

    def original_gallery_complete_scenario(scenario_name):
        if getattr(renpy.store, "original_gallery_replay_mode", False) or _in_replay:
            return
        scenario_name = str(scenario_name).upper()
        completed = original_gallery_completed()
        if scenario_name not in completed:
            persistent.original_completed_scenarios = completed | {scenario_name}
            renpy.save_persistent()

    def original_gallery_unlocked(kind, index):
        if not isinstance(index, int) or isinstance(index, bool) or index < 0:
            return False
        if kind == "cg":
            if index >= len(ORIGINAL_GALLERY_CG):
                return False
            name, path, _source = ORIGINAL_GALLERY_CG[index]
            # Also recognize existing image progress and the exported full-CG
            # persistent file. Album thumbnails do not mark either key as seen.
            return renpy.seen_image(path) or renpy.seen_image(name)
        completed = original_gallery_completed()
        if kind == "scene" and index < len(ORIGINAL_SCENE_UNLOCK_GROUPS):
            return any(all(name in completed for name in group)
                       for group in ORIGINAL_SCENE_UNLOCK_GROUPS[index])
        if kind == "ending" and index < len(ORIGINAL_ENDING_UNLOCK_SCENARIOS):
            return ORIGINAL_ENDING_UNLOCK_SCENARIOS[index] in completed
        return False

    def original_gallery_count(kind, total):
        return sum(original_gallery_unlocked(kind, index) for index in range(total))

    def original_gallery_next_cg(index, direction):
        if not isinstance(index, int) or isinstance(index, bool) or not 0 <= index < len(ORIGINAL_GALLERY_CG):
            return index
        for step in range(1, len(ORIGINAL_GALLERY_CG) + 1):
            candidate = (index + step * direction) % len(ORIGINAL_GALLERY_CG)
            if original_gallery_unlocked("cg", candidate):
                return candidate
        return index

    def original_gallery_open_cg(index):
        if original_gallery_unlocked("cg", index):
            renpy.show_screen("original_cg_viewer", cg_index=index)

    def original_gallery_resume_progress():
        # A pre-lock save can resume in the middle of a CG. Credit only the
        # currently displayed image; a route choice is not proof of completion.
        original_gallery_record_image(getattr(renpy.store, "original_current_background", None))

    config.after_load_callbacks.append(original_gallery_resume_progress)


screen original_gallery_lock(lock_x, lock_y, lock_width, lock_height):
    frame:
        xpos lock_x
        ypos lock_y
        xysize (lock_width, lock_height)
        padding (0, 0)
        background Solid("#181818")
        text _("未解锁"):
            align (0.5, 0.5)
            size 18
            color "#ffffff"


screen original_gallery_progress(kind, total_count):
    $ unlocked_count = original_gallery_count(kind, total_count)
    frame:
        xalign 1.0
        xoffset -120
        ypos 28
        padding (14, 8)
        background Solid("#181818e8")
        vbox:
            spacing 4
            text _("已解锁 [unlocked_count] / [total_count]") size 24 color "#ffffff"
            text _("在剧情中观看后解锁") size 18 color "#dddddd"
