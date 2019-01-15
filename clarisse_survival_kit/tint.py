from clarisse_survival_kit.app import *
from clarisse_survival_kit.utility import check_selection


def tint_surface_gui():
    class EventRewire(ix.api.EventObject):
        def cancel(self, sender, evtid):
            sender.get_window().hide()

        def run(self, sender, evtid):
            if check_selection([ix.selection[0]], is_kindof=["MaterialPhysicalStandard",
                                                             "OfContext"], max_num=1):
                if ix.selection[0].is_context():
                    ctx = ix.selection[0]
                else:
                    ctx = ix.selection[0].get_context()
            else:
                ix.log_warning("Please select either a Physical Standard material or its parent context.")
                return False
            ix.begin_command_batch("Tint Surface")
            tint_tx = tint_surface(ctx, color=[(r.get_value()) / 255,
                                               (g.get_value()) / 255,
                                               (b.get_value()) / 255],
                                   strength=strength.get_value(), ix=ix)
            if tint_tx:
                ix.selection.deselect_all()
                ix.selection.add(tint_tx)
            ix.end_command_batch()
            sender.get_window().hide()

    # Window creation
    clarisse_win = ix.application.get_event_window()
    window = ix.api.GuiWindow(clarisse_win, 900, 450, 400, 120)
    window.set_title('Tint diffuse')  # Window name

    # Main widget creation
    panel = ix.api.GuiPanel(window, 0, 0, window.get_width(), window.get_height())
    panel.set_constraints(ix.api.GuiWidget.CONSTRAINT_LEFT, ix.api.GuiWidget.CONSTRAINT_TOP,
                          ix.api.GuiWidget.CONSTRAINT_RIGHT, ix.api.GuiWidget.CONSTRAINT_BOTTOM)

    # Form generation
    r = ix.api.GuiNumberField(panel, 50, 10, 70, "R:")
    r.set_increment(1)
    r.set_slider_range(0, 255)
    r.enable_slider_range(True)
    g = ix.api.GuiNumberField(panel, 145, 10, 70, "G:")
    g.set_increment(1)
    g.set_slider_range(0, 255)
    g.enable_slider_range(True)
    b = ix.api.GuiNumberField(panel, 240, 10, 70, "B:")
    b.set_increment(1)
    b.set_slider_range(0, 255)
    b.enable_slider_range(True)

    strength = ix.api.GuiNumberField(panel, 129, 40, 151, "Tint strength:       ")
    strength.set_slider_range(0, 1)
    strength.enable_slider_range(True)

    close_button = ix.api.GuiPushButton(panel, 10, 90, 100, 22, "Close")
    run_button = ix.api.GuiPushButton(panel, 130, 90, 250, 22, "Apply tint")

    # init values
    r.set_value(DEFAULT_TINT_COLOR[0])
    g.set_value(DEFAULT_TINT_COLOR[1])
    b.set_value(DEFAULT_TINT_COLOR[2])
    strength.set_value(DEFAULT_TINT_STRENGTH)

    # Connect to function
    event_rewire = EventRewire()  # init the class

    event_rewire.connect(close_button, 'EVT_ID_PUSH_BUTTON_CLICK',
                         event_rewire.cancel)
    event_rewire.connect(run_button, 'EVT_ID_PUSH_BUTTON_CLICK',
                         event_rewire.run)

    # Send all info to clarisse to generate window
    window.show()
    while window.is_shown():    ix.application.check_for_events()
    window.destroy()


tint_surface_gui()
