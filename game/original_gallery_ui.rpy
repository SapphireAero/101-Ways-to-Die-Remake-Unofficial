init python:
    ORIGINAL_GALLERY_CG = (
        [entry for entry in ORIGINAL_CG if "/cg/" in entry[1]]
        + [entry for entry in ORIGINAL_CG if "/cg_r18/" in entry[1]]
    )

    ORIGINAL_SCENE_SCRIPT_FILES = [entry["scenario"] for entry in PUBLIC_CATALOG["scenes"]]
    ORIGINAL_ENDING_SCRIPT_FILES = [entry["scenario"] for entry in PUBLIC_CATALOG["endings"]]

    def original_ending_movie_path(index):
        return PUBLIC_CATALOG["endings"][index].get("movie", "")

    def original_load_gallery_script(filename):
        try:
            raw = renpy.file(filename).read()
        except Exception:
            return []

        if isinstance(raw, bytes):
            text = raw.decode("utf-8-sig", "replace")
        else:
            text = raw

        return [line.strip() for line in text.splitlines() if line.strip()]

    def original_quick_menu_visible():
        if not quick_menu or main_menu or renpy.context()._menu:
            return False
        return not any(renpy.get_screen(name) for name in (
            "original_extra_menu", "original_cg_gallery_ui", "original_sound_gallery_ui",
            "original_scene_gallery_ui", "original_ending_gallery_ui",
        ))

    def original_gallery_replay_action(kind, index):
        label, field = {
            "scene": ("original_scene_reader", "original_selected_scene"),
            "ending": ("original_ending_reader", "original_selected_ending"),
        }[kind]
        return Replay(label, scope={field: index, "original_gallery_replay_mode": True},
                      locked=not original_gallery_unlocked(kind, index))



screen original_gallery_navigation(destination="original_extra_menu", stop_sound=False):
    $ back_action = ShowMenu(destination) if destination else If(main_menu, ShowMenu("main_menu"), Return())
    if stop_sound:
        $ back_action = [Function(original_music_preview_end), back_action]
    textbutton _("返回"):
        id "original_gallery_back"
        align (0.95, 0.95)
        style "original_language_button"
        action back_action
    key "game_menu" action back_action

screen original_cg_gallery_ui():
    tag menu
    default page = 0
    $ page_count = max(1, (len(ORIGINAL_GALLERY_CG) + 5) // 6)
    add Solid("#101722")
    text _("CG 鉴赏") pos (80, 70) size 52
    use original_gallery_progress("cg", len(ORIGINAL_GALLERY_CG))
    grid 3 2:
        pos (80, 230)
        spacing 30
        for slot in range(6):
            $ index = page * 6 + slot
            if index < len(ORIGINAL_GALLERY_CG):
                button:
                    xysize (400, 270)
                    background Solid("#243449")
                    sensitive original_gallery_unlocked("cg", index)
                    action Function(original_gallery_open_cg, index)
                    if original_gallery_unlocked("cg", index):
                        add ORIGINAL_GALLERY_CG[index][1] xysize (376, 246) align (0.5, 0.5)
                    else:
                        text _("未解锁") align (0.5, 0.5)
            else:
                null width 400 height 270
    hbox:
        align (0.5, 0.85)
        spacing 50
        textbutton "<" action SetScreenVariable("page", max(0, page - 1)) sensitive page > 0
        text "[page + 1] / [page_count]"
        textbutton ">" action SetScreenVariable("page", min(page_count - 1, page + 1)) sensitive page + 1 < page_count
    use original_gallery_navigation

screen original_cg_viewer(cg_index):
    modal True
    zorder 300
    default current_index = cg_index
    add Solid("#000")
    if original_gallery_unlocked("cg", current_index):
        add ORIGINAL_GALLERY_CG[current_index][1] xysize (1440, 1080)
    textbutton _("返回") align (0.95, 0.95) action Hide("original_cg_viewer")
    key "K_LEFT" action SetScreenVariable("current_index", original_gallery_next_cg(current_index, -1))
    key "K_RIGHT" action SetScreenVariable("current_index", original_gallery_next_cg(current_index, 1))
    key "game_menu" action Hide("original_cg_viewer")

screen original_scene_gallery_ui():
    tag menu
    add Solid("#101722")
    text _("场景回放") pos (80, 70) size 52
    use original_gallery_progress("scene", len(PUBLIC_CATALOG["scenes"]))
    vbox:
        pos (100, 300)
        spacing 30
        for index, entry in enumerate(PUBLIC_CATALOG["scenes"]):
            $ caption = _(entry["title"]) if original_gallery_unlocked("scene", index) else _("未解锁")
            textbutton caption action original_gallery_replay_action("scene", index)
    use original_gallery_navigation

screen original_ending_gallery_ui():
    tag menu
    add Solid("#101722")
    text _("结局回放") pos (80, 70) size 52
    use original_gallery_progress("ending", len(PUBLIC_CATALOG["endings"]))
    vbox:
        pos (100, 300)
        spacing 30
        for index, entry in enumerate(PUBLIC_CATALOG["endings"]):
            $ caption = _(entry["title"]) if original_gallery_unlocked("ending", index) else _("未解锁")
            textbutton caption action original_gallery_replay_action("ending", index)
    use original_gallery_navigation

screen original_sound_gallery_ui():
    tag menu
    on "show" action Function(original_music_preview_begin)
    on "hide" action Function(original_music_preview_end)
    add Solid("#101722")
    text _("音乐鉴赏") pos (80, 70) size 52
    vbox:
        pos (100, 280)
        spacing 25
        text _("公开演示未附带音频素材。")
        for track, path in sorted(ORIGINAL_BGM.items()):
            if renpy.loadable(path):
                textbutton str(track) action Play("original_music_preview", path)
    use original_gallery_navigation(stop_sound=True)
