init 100 python:
    import ctypes
    import sys

    def windows_confirm_quit():
        if sys.platform != "win32":
            renpy.quit(save=True)
            return

        message_box = ctypes.windll.user32.MessageBoxW
        flags = 0x00000004 | 0x00000020 | 0x00000100 | 0x00010000 | 0x00040000
        result = message_box(
            None,
            renpy.translate_string(_("确定要退出游戏吗？")),
            renpy.translate_string(str(config.name)),
            flags,
        )

        if result == 6:
            if config.autosave_on_quit:
                renpy.force_autosave()
            renpy.quit(save=True)

    config.quit_action = windows_confirm_quit
