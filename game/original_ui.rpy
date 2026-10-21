# Shared language actions and preferences controls.
screen original_title_language():
    frame:
        xalign 1.0
        xoffset -12
        ypos 5
        padding (14, 5)
        background Solid("#000000e8")

        hbox:
            spacing 12
            yalign 0.5

            text _("语言"):
                color "#ffffff"
                size 24
                yalign 0.5

            textbutton "中文":
                id "title_chinese_language"
                action OriginalLanguageAction(None)
                style "original_language_button"

            textbutton "日本語":
                id "title_japanese_language"
                action OriginalLanguageAction("japanese")
                style "original_language_button"


style original_language_button is button:
    padding (12, 3)
    background Solid("#0000")
    hover_background Solid("#424242")
    selected_background Solid("#ffffff")
    selected_hover_background Solid("#dddddd")

style original_language_button_text is button_text:
    font gui.interface_text_font
    size 24
    color "#ffffff"
    hover_color "#ffffff"
    selected_color "#000000"
    selected_hover_color "#000000"


# Additional preferences fit into the two empty rows in the original artwork.
# All controls bind to the same Ren'Py preferences as the original image buttons.
screen original_settings_controls():
    frame:
        xpos 212
        ypos 310
        xsize 1100
        padding (14, 10)
        background Solid("#000000e8")
        hbox:
            spacing 24
            for mixer, caption, enabled, sample in (
                ("music", _("音乐音量"), config.has_music, None),
                ("sound", _("音效音量"), config.has_sound, config.sample_sound),
                ("voice", _("语音音量"), config.has_voice, config.sample_voice),
            ):
                if enabled:
                    vbox:
                        spacing 7
                        hbox:
                            spacing 12
                            text caption style "original_settings_text"
                            if sample:
                                textbutton _("测试"):
                                    style "original_settings_button"
                                    action Play(mixer, sample)
                        bar:
                            id ("original_settings_" + mixer + "_volume")
                            style "original_settings_slider"
                            value Preference(mixer + " volume")
            if config.has_music or config.has_sound or config.has_voice:
                textbutton _("全部静音"):
                    id "original_settings_mute"
                    yalign 0.5
                    style "original_settings_button"
                    action Preference("all mute", "toggle")

    frame:
        xpos 212
        ypos 650
        xsize 1100
        padding (14, 10)
        background Solid("#000000e8")
        hbox:
            spacing 24
            vbox:
                spacing 7
                text _("文字速度") style "original_settings_text"
                bar:
                    id "original_settings_text_speed"
                    style "original_settings_slider"
                    value Preference("text speed")
            vbox:
                spacing 7
                text _("自动前进时间") style "original_settings_text"
                bar:
                    id "original_settings_auto_forward"
                    style "original_settings_slider"
                    value Preference("auto-forward time")
            vbox:
                spacing 7
                text _("快进") style "original_settings_text"
                hbox:
                    spacing 10
                    textbutton _("未读文本"):
                        id "original_settings_skip_unread"
                        style "original_settings_button"
                        action Preference("skip", "toggle")
                    textbutton _("选项后继续"):
                        id "original_settings_after_choices"
                        style "original_settings_button"
                        action Preference("after choices", "toggle")


style original_settings_text is gui_text:
    font gui.interface_text_font
    size 20
    color "#ffffff"

style original_settings_button is original_language_button:
    padding (8, 3)

style original_settings_button_text is original_language_button_text:
    size 20

style original_settings_slider is gui_slider:
    xsize 230
    ysize 24
    left_bar Solid("#ffffff")
    right_bar Solid("#555555")
    thumb Solid("#dddddd", xysize=(10, 24))
    thumb_offset 5
