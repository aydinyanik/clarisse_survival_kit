from clarisse_survival_kit.settings import *
from clarisse_survival_kit.app import *


def mix_surface_gui():
    class EventRewire(ix.api.EventObject):
        def material1_picker_refresh(self, sender, evtid):
            if check_selection(ix.selection, is_kindof=["MaterialPhysicalStandard", "MaterialPhysicalBlend", "OfContext"], max_num=1):
                if ix.selection[0].is_context():
                    ctx = ix.selection[0]
                else:
                    ctx = ix.selection[0].get_context()

                if not get_mtl_from_context(ctx, ix=ix):
                    return None

                mtl1_txt.set_text(str(ctx))

                ctx1_name = ctx.get_name()
                if mtl2_txt.get_text():
                    ctx2 = ix.get_item(mtl2_txt.get_text())
                    if ctx2 and ctx2.is_context():
                        name_txt.set_text(ctx1_name + "_" + ctx2.get_name())
            else:
                ix.log_warning("Please select a valid material.\n")
                mtl1_txt.set_text("")

        def material2_picker_refresh(self, sender, evtid):
            if check_selection(ix.selection, is_kindof=["MaterialPhysicalStandard", "MaterialPhysicalBlend", "OfContext"], max_num=1):
                if ix.selection[0].is_context():
                    ctx = ix.selection[0]
                else:
                    ctx = ix.selection[0].get_context()

                if not get_mtl_from_context(ctx, ix=ix):
                    return None

                mtl2_txt.set_text(str(ctx))

                ctx2_name = ctx.get_name()
                if mtl1_txt.get_text():
                    ctx1 = ix.get_item(mtl1_txt.get_text())
                    if ctx1 and ctx1.is_context():
                        name_txt.set_text(ctx1.get_name() + "_" + ctx2_name)
            else:
                ix.log_warning("Please select a valid material.\n")
                mtl2_txt.set_text("")

        def cancel(self, sender, evtid):
            sender.get_window().hide()

        def run(self, sender, evtid):
            try:
                ctx1 = ix.get_item(mtl1_txt.get_text())
                ctx2 = ix.get_item(mtl2_txt.get_text())
                if not (ctx1.is_context() and ctx2.is_context()):
                    raise ValueError
            except BaseException as e:
                ix.log_warning("Couldn't find material: %s" % str(e))
            else:
                ix.begin_command_batch("Mix surfaces")
                surface_name = name_txt.get_text()
                blend_mtl = mix_surfaces(ctx1, ctx2,
                                         mix_surface_name=surface_name,
                                         slope_blend=slope_blend_checkbox.get_value(),
                                         invert_slope=invert_slope_checkbox.get_value(),
                                         scope_blend=scope_blend_checkbox.get_value(),
                                         triplanar_blend=triplanar_blend_checkbox.get_value(),
                                         displacement_blend=displacement_blend_checkbox.get_value(),
                                         height_blend=height_blend_checkbox.get_value(),
                                         fractal_blend=fractal_blend_checkbox.get_value(),
                                         ao_blend=ao_blend_checkbox.get_value(),
                                         ix=ix)
                if blend_mtl:
                    ix.selection.deselect_all()
                    ix.selection.add(blend_mtl)
                ix.end_command_batch()
                sender.get_window().hide()

    # Window creation
    clarisse_win = ix.application.get_event_window()
    window = ix.api.GuiWindow(clarisse_win, 900, 450, 400, 470)  # Parent, X position, Y position, Width, Height
    window.set_title('Material mixer')  # Window name

    # Main widget creation
    panel = ix.api.GuiPanel(window, 0, 0, window.get_width(), window.get_height())
    panel.set_constraints(ix.api.GuiWidget.CONSTRAINT_LEFT, ix.api.GuiWidget.CONSTRAINT_TOP,
                          ix.api.GuiWidget.CONSTRAINT_RIGHT, ix.api.GuiWidget.CONSTRAINT_BOTTOM)

    # Form generation
    mt1_label = ix.api.GuiLabel(panel, 10, 10, 380, 22, "Material 1:")
    # mtl1_disp_label = ix.api.GuiLabel(panel, 205, 10, 380, 22, "Displacement 1:")
    mtl1_txt = ix.api.GuiLineEdit(panel, 10, 40, 385, 22)
    # mtl1_disp_txt = ix.api.GuiLineEdit(panel, 205, 40, 185, 22)
    mtl1_btn= ix.api.GuiPushButton(panel, 10, 70, 380, 22, "Add selected material")

    mtl2_label = ix.api.GuiLabel(panel, 10, 100, 380, 22, "Material 2:")
    # mtl2_disp_label = ix.api.GuiLabel(panel, 205, 100, 380, 22, "Displacement 2:")
    mtl2_txt = ix.api.GuiLineEdit(panel, 10, 130, 385, 22)
    # mtl2_disp_txt = ix.api.GuiLineEdit(panel, 205, 130, 185, 22)
    mtl2_btn= ix.api.GuiPushButton(panel, 10, 160, 380, 22, "Add selected material")

    name_label = ix.api.GuiLabel(panel, 10, 190, 150, 22, "Surface name:")
    name_txt = ix.api.GuiLineEdit(panel, 100, 190, 290, 22)
    displacement_blend_label = ix.api.GuiLabel(panel, 10, 220, 150, 22,
                                             "Displacement blend: ")
    displacement_blend_checkbox = ix.api.GuiCheckbox(panel, 205, 220, "")
    fractal_blend_label = ix.api.GuiLabel(panel, 10, 250, 150, 22,
                                             "Fractal blend: ")
    fractal_blend_checkbox = ix.api.GuiCheckbox(panel, 205, 250, "")
    triplanar_blend_label = ix.api.GuiLabel(panel, 10, 280, 150, 22,
                                             "Triplanar blend: ")
    triplanar_blend_checkbox = ix.api.GuiCheckbox(panel, 205, 280, "")
    slope_blend_label = ix.api.GuiLabel(panel, 10, 310, 150, 22,
                                             "Slope blend: ")
    slope_blend_checkbox = ix.api.GuiCheckbox(panel, 205, 310, "")
    invert_slope_label = ix.api.GuiLabel(panel, 240, 310, 100, 22,
                                             "Invert: ")
    invert_slope_checkbox = ix.api.GuiCheckbox(panel, 370, 310, "")
    scope_blend_label = ix.api.GuiLabel(panel, 10, 340, 150, 22,
                                             "Scope blend: ")
    scope_blend_checkbox = ix.api.GuiCheckbox(panel, 205, 340, "")
    ao_blend_label = ix.api.GuiLabel(panel, 10, 370, 150, 22,
                                             "Occlusion blend: ")
    ao_slope_label2 = ix.api.GuiLabel(panel, 240, 370, 150, 22, "*Slow with displacement")
    ao_blend_checkbox = ix.api.GuiCheckbox(panel, 205, 370, "")
    height_blend_label = ix.api.GuiLabel(panel, 10, 400, 150, 22,
                                             "Height blend: ")
    height_blend_checkbox = ix.api.GuiCheckbox(panel, 205, 400, "")
    cancel_btn = ix.api.GuiPushButton(panel, 10, 430, 100, 22, "Close")  # The cancel button (destroy the script window)
    run_btn = ix.api.GuiPushButton(panel, 130, 430, 250, 22, "Mix materials")  # The run button to run your script

    # init values
    fractal_blend_checkbox.set_value(True)

    # Connect to function
    event_rewire = EventRewire()  # init the class
    event_rewire.connect(mtl1_txt, 'EVT_ID_LINE_EDIT_CHANGED',
                         event_rewire.material1_picker_refresh)
    event_rewire.connect(mtl2_txt, 'EVT_ID_LINE_EDIT_CHANGED',
                         event_rewire.material2_picker_refresh)
    event_rewire.connect(mtl1_btn, 'EVT_ID_PUSH_BUTTON_CLICK',
                         event_rewire.material1_picker_refresh)
    event_rewire.connect(mtl2_btn, 'EVT_ID_PUSH_BUTTON_CLICK',
                         event_rewire.material2_picker_refresh)
    event_rewire.connect(cancel_btn, 'EVT_ID_PUSH_BUTTON_CLICK',
                         event_rewire.cancel)
    event_rewire.connect(run_btn, 'EVT_ID_PUSH_BUTTON_CLICK',
                         event_rewire.run)

    # Send all info to clarisse to generate window
    window.show()
    while window.is_shown():    ix.application.check_for_events()
    window.destroy()


mix_surface_gui()
