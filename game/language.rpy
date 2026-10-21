# Project language switching.
#
# Ren'Py's built-in Language action changes the translator, but this project
# also has a JSON-backed scenario reader. Keep both layers in sync whenever the
# player changes language from the preferences screen.

init python:
    ORIGINAL_SUPPORTED_LANGUAGES = (None, "japanese")

    def original_normalize_language(language):
        if language in ORIGINAL_SUPPORTED_LANGUAGES:
            return language
        return None

    def original_set_language(language):
        language = original_normalize_language(language)

        # Force the rebuild even when Ren'Py already thinks the language is
        # unchanged. This is important after returning from a save or after
        # entering a screen that cached translated text.
        renpy.change_language(language, force=True, rebuild=True)

        # The scenario reader caches data per language. Clearing this cache
        # makes a language change affect an already running route as well as
        # the next route that is opened.
        if "_original_scenario_cache" in globals():
            _original_scenario_cache.clear()
        if "_original_text_translation_cache" in globals():
            _original_text_translation_cache.clear()
        if "_original_translation_tables" in globals():
            _original_translation_tables.clear()

        renpy.restart_interaction()

    class OriginalLanguageAction(Action):
        def __init__(self, language):
            self.language = original_normalize_language(language)

        def __call__(self):
            original_set_language(self.language)

        def get_selected(self):
            return renpy.game.preferences.language == self.language

        def get_sensitive(self):
            return self.language is None or self.language in renpy.known_languages()
