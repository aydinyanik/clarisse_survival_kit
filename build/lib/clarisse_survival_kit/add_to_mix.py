from clarisse_survival_kit.app import *
from clarisse_survival_kit.utility import get_mtl_from_context, check_selection


def add_mix_surface_gui():
    class EventRewire(ix.api.EventObject):
        def srf1_picker_refresh(self, sender, evtid):
            if check_selection(ix.selection,
                               is_kindof=["MaterialPhysicalStandard", "MaterialPhysicalBlend", "OfContext"], min_num=1):
                ctxs = []
                for selection in ix.selection:
                    if selection.is_context():
                        ctx = selection
                    else:
                        ctx = selection.get_context()

                    if not get_mtl_from_context(ctx, ix=ix):
                        return None

                    ctxs.append(str(ctx))
                if srf2_txt.get_text():
                    ctx2 = ix.get_item(srf2_txt.get_text())
                    name_txt.set_text(ctx2.get_name() + MIX_SUFFIX)
                srf1_txt.set_text(str(IMPORTER_PATH_DELIMITER.join(ctxs)))
            else:
                ix.log_warning("Please select a valid material.\n")
                srf1_txt.set_text("")

        def mix_ctx_picker_refresh(self, sender, evtid):
            if check_selection(ix.selection,
                               is_kindof=["OfContext"], max_num=1):
                ctx = ix.selection[0]

                if not get_items(ctx, kind=['MaterialPhysicalBlend'], return_first_hit=True, ix=ix):
                    ix.log_warning("Please select a valid mix context.\n")
                    return None
                if not get_items(ctx, kind=['TextureMultiBlend'], return_first_hit=True, max_depth=1, ix=ix):
                    ix.log_warning("Please select a valid mix context.\n")
                    return None

                srf2_txt.set_text(str(ctx))

                ctx2_name = ctx.get_name()
                name_txt.set_text(ctx2_name + MIX_SUFFIX)
                ix.selection.deselect_all()
                ix.selection.add(ctx.get_parent())
            else:
                ix.log_warning("Please select a valid mix context.\n")
                srf2_txt.set_text("")

        def cancel(self, sender, evtid):
            sender.get_window().hide()

        def run(self, sender, evtid):
            try:
                ctxs = []
                for ctx_name in srf1_txt.get_text().split(IMPORTER_PATH_DELIMITER):
                    ctx = ix.get_item(ctx_name)
                    ctxs.append(ctx)
                    if not ctx.is_context():
                        raise ValueError
                ctx2 = ix.get_item(srf2_txt.get_text())
                if not ctx2.is_context():
                    raise ValueError
            except BaseException as e:
                ix.log_warning("Couldn't find material: %s" % str(e))
            else:
                ix.begin_command_batch("Add Surface to Mix")
                mix_ctx = mix_surfaces(ctxs, ctx2,
                                       mode="add",
                                       displacement_blend=displacement_blend_checkbox.get_value(),
                                       assign_mtls=assign_mtls_checkbox.get_value(),
                                       ix=ix)
                if mix_ctx:
                    ix.selection.deselect_all()
                    ix.selection.add(mix_ctx)
                ix.end_command_batch()
                sender.get_window().hide()

    # Window creation
    clarisse_win = ix.application.get_event_window()
    window = ix.api.GuiWindow(clarisse_win, 900, 450, 400, 280)  # Parent, X position, Y position, Width, Height
    window.set_title('Material mixer')  # Window name

    # Main widget creation
    panel = ix.api.GuiPanel(window, 0, 0, window.get_width(), window.get_height())
    panel.set_constraints(ix.api.GuiWidget.CONSTRAINT_LEFT, ix.api.GuiWidget.CONSTRAINT_TOP,
                          ix.api.GuiWidget.CONSTRAINT_RIGHT, ix.api.GuiWidget.CONSTRAINT_BOTTOM)

    # Form generation
    srf1_label = ix.api.GuiLabel(panel, 10, 10, 380, 22, "Base Surface(s):")
    srf1_txt = ix.api.GuiLineEdit(panel, 10, 40, 385, 22)
    srf1_btn = ix.api.GuiPushButton(panel, 10, 70, 380, 22, "Add selected material(s)")

    srf2_label = ix.api.GuiLabel(panel, 10, 100, 380, 22, "Mix Context:")
    srf2_txt = ix.api.GuiLineEdit(panel, 10, 130, 385, 22)
    srf2_btn = ix.api.GuiPushButton(panel, 10, 160, 380, 22, "Add selected mix")

    displacement_blend_label = ix.api.GuiLabel(panel, 10, 190, 150, 22,
                                               "Displacement blend: ")
    displacement_blend_checkbox = ix.api.GuiCheckbox(panel, 205, 190, "")

    assign_mtls_label = ix.api.GuiLabel(panel, 10, 220, 150, 22,
                                        "Assign new materials: ")
    assign_mtls_checkbox = ix.api.GuiCheckbox(panel, 205, 220, "")

    cancel_btn = ix.api.GuiPushButton(panel, 10, 250, 100, 22, "Close")  # The cancel button (destroy the script window)
    run_btn = ix.api.GuiPushButton(panel, 130, 250, 250, 22, "Add to Mix")  # The run button to run your script

    # init values
    assign_mtls_checkbox.set_value(True)

    # Connect to function
    event_rewire = EventRewire()  # init the class
    event_rewire.connect(srf1_txt, 'EVT_ID_LINE_EDIT_CHANGED',
                         event_rewire.srf1_picker_refresh)
    event_rewire.connect(srf2_txt, 'EVT_ID_LINE_EDIT_CHANGED',
                         event_rewire.mix_ctx_picker_refresh)
    event_rewire.connect(srf1_btn, 'EVT_ID_PUSH_BUTTON_CLICK',
                         event_rewire.srf1_picker_refresh)
    event_rewire.connect(srf2_btn, 'EVT_ID_PUSH_BUTTON_CLICK',
                         event_rewire.mix_ctx_picker_refresh)
    event_rewire.connect(cancel_btn, 'EVT_ID_PUSH_BUTTON_CLICK',
                         event_rewire.cancel)
    event_rewire.connect(run_btn, 'EVT_ID_PUSH_BUTTON_CLICK',
                         event_rewire.run)

    # Send all info to clarisse to generate window
    window.show()
    while window.is_shown():    ix.application.check_for_events()
    window.destroy()


add_mix_surface_gui()
