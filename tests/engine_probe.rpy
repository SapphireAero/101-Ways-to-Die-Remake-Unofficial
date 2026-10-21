init 999 python:
    config.save_persistent = False
    config.autosave_on_quit = False
    config.savedir = __import__("os").path.join(config.basedir, "probe-saves")

    def public_probe():
        import json
        import traceback
        import pathlib
        import pygame_sdl2
        output = pathlib.Path(config.basedir)
        report = {"screens": [], "routes": []}
        try:
            renpy.display.interface.start()
            for language in (None, "japanese"):
                renpy.change_language(language, force=True, rebuild=True)
                for name in ("main_menu", "original_settings_menu", "original_extra_menu", "original_cg_gallery_ui", "original_scene_gallery_ui", "original_ending_gallery_ui", "original_sound_gallery_ui", "load", "save", "history", "about", "say", "choice"):
                    args = {"who": None, "what": "公开演示 / テキスト"} if name == "say" else ({"items": [("蓝色路线", 0), ("琥珀路线", 1)]} if name == "choice" else {})
                    # Choice screen expects MenuEntry objects, supplied below.
                    if name == "choice":
                        from collections import namedtuple
                        Item = namedtuple("Item", "caption action chosen args kwargs")
                        args = {"items": [Item("蓝色路线", NullAction(), False, (), {}), Item("琥珀路线", NullAction(), False, (), {})]}
                    renpy.show_screen(name, **args)
                    screen = renpy.get_screen(name)
                    renpy.display.screen.updated_screens.clear()
                    screen.update()
                    rendered = renpy.render(screen, 1440, 1080, 0, 0)
                    surface = renpy.display.draw.render_to_texture(rendered, True)
                    if language is None and name in ("main_menu", "original_settings_menu", "say"):
                        pygame_sdl2.image.save(surface, str(output / (name + ".png")))
                    report["screens"].append([name, language or "schinese", [surface.get_width(), surface.get_height()]])
                    renpy.hide_screen(name)

            renpy.change_language(None, force=True, rebuild=True)
            real_say = renpy.exports.say
            text_log = []
            def probe_say(who, what, *args, **kwargs):
                if original_dialogue_context:
                    text_log.append([original_scenario_name, original_dynamic_text(), original_dialogue_label()])
                kwargs["interact"] = False
                result = real_say(who, what, *args, **kwargs)
                if original_dialogue_context and original_scenario_name == "DEMO_A.FOB":
                    screen = renpy.get_screen("say")
                    if screen:
                        renpy.display.screen.updated_screens.clear()
                        screen.update()
                        rendered = renpy.render(screen, 1440, 1080, 0, 0)
                        surface = renpy.display.draw.render_to_texture(rendered, True)
                        pygame_sdl2.image.save(surface, str(output / "actual-dialogue.png"))
                return result
            renpy.exports.say = probe_say
            renpy.pause = lambda *args, **kwargs: False
            renpy.exports.pause = renpy.pause
            renpy.with_statement = lambda *args, **kwargs: None
            renpy.exports.with_statement = renpy.with_statement
            for language, branch in ((None, 0), (None, 1), ("japanese", 0), ("japanese", 1)):
                renpy.change_language(language, force=True, rebuild=True)
                text_log[:] = []
                persistent.original_completed_scenarios = set()
                persistent._seen_images.clear()
                renpy.display_menu = lambda *args, **kwargs: branch
                renpy.exports.display_menu = renpy.display_menu
                renpy.call_in_new_context("original_script_reader")
                names = [entry[0] for entry in text_log]
                expected = "DEMO_A.FOB" if branch == 0 else "DEMO_B.FOB"
                other = "DEMO_B.FOB" if branch == 0 else "DEMO_A.FOB"
                assert names.count(expected) == 2, names
                assert names.count("DEMO_NOTE.FOB") == 1, names
                assert names.count("DEMO_END.FOB") == 1, names
                assert other not in names, names
                assert original_gallery_unlocked("cg", branch)
                assert not original_gallery_unlocked("cg", 1 - branch)
                assert original_gallery_unlocked("scene", branch)
                assert original_gallery_unlocked("ending", 0)
                assert len(original_scenario_call_stack) == 0
                assert text_log[-1][0] == "DEMO_END.FOB"
                report["routes"].append({"language": language or "schinese", "branch": branch, "text_scenarios": names, "native_labels": [entry[2] for entry in text_log], "unlocked_cg": original_gallery_count("cg", len(ORIGINAL_GALLERY_CG))})
            for name, path, source in ORIGINAL_GALLERY_CG:
                drawable = Image(path)
                rendered = renpy.render(drawable, 1440, 1080, 0, 0)
                surface = renpy.display.draw.render_to_texture(rendered, True)
                assert surface.get_size() == (1440, 1080)
                renpy.mark_image_seen(path)
            for name, args in (("original_cg_gallery_ui", {}), ("original_cg_viewer", {"cg_index": 0})):
                renpy.show_screen(name, **args)
                screen = renpy.get_screen(name)
                renpy.display.screen.updated_screens.clear()
                screen.update()
                rendered = renpy.render(screen, 1440, 1080, 0, 0)
                surface = renpy.display.draw.render_to_texture(rendered, True)
                pygame_sdl2.image.save(surface, str(output / (name + ".png")))
                renpy.hide_screen(name)
            report["cg_rendered"] = len(ORIGINAL_GALLERY_CG)
            report["ok"] = True
        except Exception:
            report["error"] = traceback.format_exc()
        (output / "probe-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        renpy.quit(status=0 if report.get("ok") else 1, save=False)

    config.start_callbacks.append(public_probe)
