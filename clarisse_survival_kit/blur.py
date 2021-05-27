from clarisse_survival_kit.app import *
from clarisse_survival_kit.utility import check_selection, blur_tx


def blur_textures_gui():
    class EventRewire(ix.api.EventObject):
        # These are the called functions by the connect. It is more flexible to make a function for each button
        def cancel(self, sender, evtid):
            sender.get_window().hide()  # Hide the window, if it is done, the window is destroy

        def run(self, sender, evtid):
            if ix.selection.get_count() == 0:
                ix.log_warning("Please select one or more texture objects.")
            else:
                textures = []
                for selected in ix.selection:
                    if check_selection([selected], is_kindof=["Texture"]):
                        textures.append(selected)
                    else:
                        ix.log_warning("One or more selected items are not texture objects.")
                ix.begin_command_batch("Blur textures")
                blurred_textures = []
                for texture in textures:
                    blurred_textures.append(blur_tx(texture, radius=radius_field.get_value(),
                                                    quality=int(quality_field.get_value()),
                                                    ix=ix))
                if blurred_textures:
                    ix.selection.deselect_all()
                    for blurred_tx in blurred_textures:
                        ix.selection.add(blurred_tx)
                ix.end_command_batch()
            sender.get_window().hide()

    # Window creation
    clarisse_win = ix.application.get_event_window()
    window = ix.api.GuiWindow(clarisse_win, 900, 450, 400, 120)  # Parent, X position, Y position, Width, Height
    window.set_title('Blur selected textures')  # Window name

    # Main widget creation <= this is the correct way to make a GUI, make a default widget and add inside what you want
    panel = ix.api.GuiPanel(window, 0, 0, window.get_width(), window.get_height())
    panel.set_constraints(ix.api.GuiWidget.CONSTRAINT_LEFT, ix.api.GuiWidget.CONSTRAINT_TOP,
                          ix.api.GuiWidget.CONSTRAINT_RIGHT, ix.api.GuiWidget.CONSTRAINT_BOTTOM)

    # Form generation
    radius_field = ix.api.GuiNumberField(panel, 70, 10, 320, "Blur radius")
    quality_field = ix.api.GuiNumberField(panel, 70, 40, 320, "Blur quality")
    cancelBtn = ix.api.GuiPushButton(panel, 10, 90, 100, 22, "Cancel")  # The cancel button (destroy the script window)
    runBtn = ix.api.GuiPushButton(panel, 130, 90, 250, 22, "Apply")  # The run button to run your script

    # init values
    radius_field.set_value(0.01)
    quality_field.set_slider_range(1, 32)
    quality_field.set_increment(1)
    quality_field.enable_slider_range(True)
    quality_field.set_value(DEFAULT_BLUR_QUALITY)

    # Connect to function
    event_rewire = EventRewire()  # init the class

    event_rewire.connect(cancelBtn, 'EVT_ID_PUSH_BUTTON_CLICK',
                         event_rewire.cancel)  # connect(item_to_listen, what_we_are_listening, function_called)
    event_rewire.connect(runBtn, 'EVT_ID_PUSH_BUTTON_CLICK',
                         event_rewire.run)  # connect(item_to_listen, what_we_are_listening, function_called)

    # Send all info to clarisse to generate window
    window.show()
    while window.is_shown():    ix.application.check_for_events()
    window.destroy()


blur_textures_gui()
