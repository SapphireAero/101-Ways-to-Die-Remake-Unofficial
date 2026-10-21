# Presentation calls recovered from the original FOB bytecode. TextOn is
# anchored before its text block, since the source passes the block as an arg.
init python:
    def original_presentation_execute(event, restoring=False):
        command = event["command"]
        if command == "WaitTime":
            if not restoring:
                # The original timer converts ticks to milliseconds at 60 Hz.
                renpy.pause(max(0, event["ticks"]) / 60.0)
        elif command == "WaitKey":
            if not restoring:
                renpy.pause()
        else:
            # An explicit off remains in force through scene changes and
            # pauses. TextOn re-enables Ren'Py's automatic window behaviour.
            store._window_auto = command == "TextOn"
            transition = None if restoring or command.endswith("Direct") or command == "TextOn" else False
            if command in ("TextOn", "TextWindowOn", "TextWindowOnDirect"):
                _window_show(transition)
            elif command in ("TextClose", "TextWindowOff", "TextWindowOffDirect"):
                _window_hide(transition)
