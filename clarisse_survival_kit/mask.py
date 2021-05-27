from clarisse_survival_kit.settings import *
from clarisse_survival_kit.app import *
import logging
import os


def get_blend_nodes(items=None):
    blend_nodes = []
    if items is None:
        items = ix.selection
    for item in items:
        print(str(item))
        kind = ['TextureBlend', 'MaterialPhysicalBlend']
        if item.is_context():
            ctx_textures = get_items(item, kind=kind, ix=ix)
            blend_nodes = blend_nodes + get_blend_nodes(ctx_textures)
        elif item.get_class_name() in kind:
            if not item.attrs.mix.attr.get_texture():
                blend_nodes.append(item)
            else:
                print(str(item) + ' was ignored because mix attribute is already connected.')
    return blend_nodes


def mask_gui():
    logging.debug("Converter GUI started")

    class EventRewire(ix.api.EventObject):
        def add_selected(self, sender, evtid):
            textures = get_blend_nodes()
            for tx in textures:
                if selection_list.find_item_by_name(str(tx)) == -1:
                    selection_list.add_item(str(tx))

        def remove_selected(self, sender, evtid):
            if selection_list.get_selected_index() >= 0:
                selection_list.remove_item(selection_list.get_selected_index())

        def cancel(self, sender, evtid):
            sender.get_window().hide()

        def run(self, sender, evtid):
            ix.begin_command_batch("Mask")
            count = selection_list.get_item_count()
            blend_items = []
            for i in range(0, count):
                blend_items.append(ix.get_item(selection_list.get_item_name(i)))
            mask_blend_nodes(blend_items,
                             mix_name=name_txt.get_text(),
                             height_blend=height_blend_checkbox.get_value(),
                             fractal_blend=fractal_blend_checkbox.get_value(),
                             scope_blend=scope_blend_checkbox.get_value(),
                             slope_blend=slope_blend_checkbox.get_value(),
                             triplanar_blend=triplanar_blend_checkbox.get_value(),
                             ao_blend=ao_blend_checkbox.get_value(),
                             ix=ix)
            ix.application.check_for_events()
            ix.end_command_batch()

    # Window creation
    clarisse_win = ix.application.get_event_window()
    window = ix.api.GuiWindow(clarisse_win, 900, 450, 600, 440)  # Parent, X position, Y position, Width, Height
    window.set_title('Mask blend nodes')  # Window name

    # Main widget creation
    panel = ix.api.GuiPanel(window, 0, 0, window.get_width(), window.get_height())
    panel.set_constraints(ix.api.GuiWidget.CONSTRAINT_LEFT, ix.api.GuiWidget.CONSTRAINT_TOP,
                          ix.api.GuiWidget.CONSTRAINT_RIGHT, ix.api.GuiWidget.CONSTRAINT_BOTTOM)

    # Form generation
    separator_label1 = ix.api.GuiLabel(panel, 10, 10, 380, 22, "[ BLEND NODES: ]")
    separator_label1.set_text_color(ix.api.GMathVec3uc(128, 128, 128))

    textures = get_blend_nodes()
    selection_list = ix.api.GuiListView(panel, 10, 40, 580, 90)
    for texture in textures:
        selection_list.add_item(str(texture))
    selection_list.set_mouse_over_selection(False)
    add_button = ix.api.GuiPushButton(panel, 10, 140, 450, 22, "Add selected")
    remove_button = ix.api.GuiPushButton(panel, 480, 140, 100, 22, "Remove")

    separator_label2 = ix.api.GuiLabel(panel, 10, 180, 380, 22, "[ SELECTORS: ]")
    separator_label2.set_text_color(ix.api.GMathVec3uc(128, 128, 128))

    fractal_blend_label = ix.api.GuiLabel(panel, 10, 210, 150, 22,
                                          "Fractal blend: ")
    fractal_blend_checkbox = ix.api.GuiCheckbox(panel, 205, 210, "")
    fractal_blend_checkbox.set_value(True)
    triplanar_blend_label = ix.api.GuiLabel(panel, 10, 240, 150, 22,
                                            "Triplanar blend: ")
    triplanar_blend_checkbox = ix.api.GuiCheckbox(panel, 205, 240, "")
    slope_blend_label = ix.api.GuiLabel(panel, 10, 270, 150, 22,
                                        "Slope blend: ")
    slope_blend_checkbox = ix.api.GuiCheckbox(panel, 205, 270, "")
    scope_blend_label = ix.api.GuiLabel(panel, 320, 210, 150, 22,
                                        "Scope blend: ")
    scope_blend_checkbox = ix.api.GuiCheckbox(panel, 570, 210, "")
    ao_blend_label = ix.api.GuiLabel(panel, 320, 240, 150, 22,
                                     "Occlusion blend: ")
    ao_blend_checkbox = ix.api.GuiCheckbox(panel, 570, 240, "")
    height_blend_label = ix.api.GuiLabel(panel, 320, 270, 190, 22,
                                         "Height blend: ")
    height_blend_checkbox = ix.api.GuiCheckbox(panel, 570, 270, "")

    separator_label3 = ix.api.GuiLabel(panel, 10, 320, 380, 22, "[ NAME: ]")
    separator_label3.set_text_color(ix.api.GMathVec3uc(128, 128, 128))

    name_label = ix.api.GuiLabel(panel, 10, 350, 150, 22, "Mix name or suffix:")
    name_txt = ix.api.GuiLineEdit(panel, 200, 350, 390, 22)
    name_txt.set_text('mix')

    close_button = ix.api.GuiPushButton(panel, 10, 400, 100, 22, "Close")
    run_button = ix.api.GuiPushButton(panel, 330, 400, 250, 22, "Apply")


    # Connect to function
    event_rewire = EventRewire()  # init the class
    event_rewire.connect(add_button, 'EVT_ID_PUSH_BUTTON_CLICK',
                         event_rewire.add_selected)
    event_rewire.connect(remove_button, 'EVT_ID_PUSH_BUTTON_CLICK',
                         event_rewire.remove_selected)
    event_rewire.connect(close_button, 'EVT_ID_PUSH_BUTTON_CLICK',
                         event_rewire.cancel)
    event_rewire.connect(run_button, 'EVT_ID_PUSH_BUTTON_CLICK',
                         event_rewire.run)

    # Send all info to clarisse to generate window
    window.show()
    while window.is_shown():    ix.application.check_for_events()
    window.destroy()


mask_gui()
