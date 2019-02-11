from clarisse_survival_kit.settings import *
from clarisse_survival_kit.app import *
import logging


def import_asset_gui(**kwargs):
    logging.debug("Import Asset GUI started")
    ix = get_ix(kwargs.get('ix'))
    auto_cycle_name = 'Auto (Cycle)'

    class EventRewire(ix.api.EventObject):
        def color_space_preset_refresh(self, sender, evtid):
            if sender == color_space_presets_list:
                color_space_preset = DEFAULT_COLOR_SPACES.copy()
                color_space_preset.update(COLOR_SPACE_PRESETS.get(sender.get_selected_item_name().lower()))
                if color_space_preset:
                    for key, color_space_list_button in color_space_list_buttons.iteritems():
                        for color_space in color_spaces:
                            if color_space_preset.get(key) and color_space in color_space_preset[key]:
                                color_space_list_button.set_selected_item_by_index(color_spaces.index(color_space))
            else:
                select_id = 0
                for preset_index, preset in COLOR_SPACE_PRESETS.items():
                    passes = True
                    color_space_preset = DEFAULT_COLOR_SPACES.copy()
                    color_space_preset.update(preset)
                    for key, color_space_list_button in color_space_list_buttons.iteritems():
                        if not color_space_list_button.get_selected_item_name() in color_space_preset[key]:
                            passes = False
                            break
                    if passes:
                        select_id = COLOR_SPACE_PRESETS.keys().index(preset_index) + 1
                color_space_presets_list.set_selected_item_by_index(select_id)
            return None

        def path_refresh(self, sender, evtid):
            directory = ix.api.GuiWidget.open_folder(ix.application, '',
                                                     'Surface directory')  # Summon the window to choose files
            if directory:
                if os.path.isdir(str(directory)):
                    path_txt.set_text(str(directory))
                else:
                    ix.log_warning("Invalid directory: %s" % str(directory))

        def cancel(self, sender, evtid):
            sender.get_window().hide()

        def run(self, sender, evtid):
            ix.begin_command_batch("Import Asset")
            directory_txt = path_txt.get_text()
            if directory_txt:
                directories = directory_txt.split(IMPORTER_PATH_DELIMITER)
                for directory in directories:
                    if os.path.isdir(directory):
                        logging.debug("Import Controller called")
                        provider_name = provider_list.get_selected_item_name().lower()
                        if provider_name == auto_cycle_name.lower():
                            provider_name = None
                        resolution = resolution_list.get_selected_item_name()
                        if resolution == 'Auto':
                            resolution = None
                        lod = lod_list.get_selected_item_name()
                        if lod == 'High':
                            lod = -1
                        else:
                            lod = int(lod)
                        color_space_selection = {}
                        for color_space_key, color_space_list_button in color_space_list_buttons.items():
                            color_space_selection[color_space_key] = color_space_list_button.get_selected_item_name()
                        surface = import_controller(directory,
                                                    provider_name=provider_name,
                                                    projection_type=mapping_list.get_selected_item_name().lower(),
                                                    clip_opacity=clip_opacity_checkbox.get_value(),
                                                    object_space=os_list.get_selected_item_index(),
                                                    color_spaces=color_space_selection,
                                                    triplanar_blend=triplanar_blend_field.get_value(),
                                                    ior=ior_field.get_value(),
                                                    metallic_ior=metallic_ior_field.get_value(),
                                                    resolution=resolution,
                                                    lod=lod,
                                                    ix=ix)
                        if surface:
                            ix.selection.deselect_all()
                            ix.selection.add(surface.mtl)
                    else:
                        ix.log_warning("Invalid directory: %s" % directory)
            else:
                ix.log_warning("No directory specified")
            ix.end_command_batch()

    # Window creation
    clarisse_win = ix.application.get_event_window()
    window = ix.api.GuiWindow(clarisse_win, 900, 450, 400, 640)  # Parent, X position, Y position, Width, Height
    window.set_title('Asset importer')  # Window name

    # Main widget creation
    panel = ix.api.GuiPanel(window, 0, 0, window.get_width(), window.get_height())
    panel.set_constraints(ix.api.GuiWidget.CONSTRAINT_LEFT, ix.api.GuiWidget.CONSTRAINT_TOP,
                          ix.api.GuiWidget.CONSTRAINT_RIGHT, ix.api.GuiWidget.CONSTRAINT_BOTTOM)

    # Form generation
    separator_label1 = ix.api.GuiLabel(panel, 10, 10, 380, 22, "[ ASSET DIRECTORY: ]")
    separator_label1.set_text_color(ix.api.GMathVec3uc(128, 128, 128))
    path_button = ix.api.GuiPushButton(panel, 320, 40, 60, 22, "Browse")
    path_txt = ix.api.GuiLineEdit(panel, 10, 40, 300, 22)

    separator_label2 = ix.api.GuiLabel(panel, 10, 70, 380, 22, "[ CONTENT PROVIDER: ]")
    separator_label2.set_text_color(ix.api.GMathVec3uc(128, 128, 128))

    provider_label = ix.api.GuiLabel(panel, 10, 100, 150, 22, "Provider: ")
    provider_list = ix.api.GuiListButton(panel, 180, 100, 120, 22)
    provider_list.add_item(auto_cycle_name)
    provider_list.add_separator()
    for object_space_option in PROVIDERS:
        provider_list.add_item(object_space_option.capitalize())
    provider_list.set_selected_item_by_index(0)

    separator_label3 = ix.api.GuiLabel(panel, 10, 130, 380, 22, "[ MAPPING ]")
    separator_label3.set_text_color(ix.api.GMathVec3uc(128, 128, 128))

    mapping_label = ix.api.GuiLabel(panel, 10, 160, 180, 22, "Projection: ")
    mapping_types = ['uv', 'triplanar', 'cubic', 'spherical', 'planar', 'cylindrical']
    mapping_list = ix.api.GuiListButton(panel, 180, 160, 120, 22)
    for mapping_type in mapping_types:
        mapping_list.add_item(mapping_type.capitalize())
    mapping_list.set_selected_item_by_index(1)

    os_label = ix.api.GuiLabel(panel, 10, 190, 150, 22, "Object Space: ")
    os_list = ix.api.GuiListButton(panel, 180, 190, 120, 22)
    for object_space_option in ['Object (Base)', 'Object (Deformed)', 'Instance', 'World']:
        os_list.add_item(object_space_option)

    triplanar_label = ix.api.GuiLabel(panel, 10, 220, 150, 22,
                                             "Triplanar blend:")
    triplanar_blend_field = ix.api.GuiNumberField(panel, 180, 220, 50, "")
    triplanar_blend_field.set_slider_range(0, 1)
    triplanar_blend_field.set_increment(0.1)
    triplanar_blend_field.enable_slider_range(True)

    resolution_label = ix.api.GuiLabel(panel, 10, 250, 180, 22, "Resolution: ")
    resolution_types = ['Auto'] + IMAGE_RESOLUTIONS
    resolution_list = ix.api.GuiListButton(panel, 180, 250, 120, 22)
    for resolution_type in resolution_types:
        resolution_list.add_item(resolution_type)
    resolution_list.set_selected_item_by_index(0)

    separator_label4 = ix.api.GuiLabel(panel, 10, 280, 380, 22, "[ COLOR SPACES: ]")
    separator_label4.set_text_color(ix.api.GMathVec3uc(128, 128, 128))

    color_space_presets_list = ix.api.GuiListButton(panel, 270, 280, 120, 22)
    color_space_presets_list.add_item('Custom')
    color_space_presets_list.add_separator()
    for key, color_space_preset in COLOR_SPACE_PRESETS.items():
        color_space_presets_list.add_item(key.capitalize())
    color_space_presets_list.set_selected_item_by_index(1)

    color_spaces = []
    for name in ix.api.ColorIO.get_color_space_names():
        color_spaces.append(name)

    offset_y = 280

    color_space_list_buttons = {}
    color_space_labels = {}
    i = 0
    color_space_items = DEFAULT_COLOR_SPACES.copy()
    color_space_items.pop('preview')

    for key, options in color_space_items.items():
        offset_x = 10 if (i % 2) == 0 else 220
        if (i % 2) == 0:
            offset_y += 30
        color_space_labels[key] = ix.api.GuiLabel(panel, offset_x, offset_y, 150, 22,
                                                                  ("%s: " % key).capitalize())
        gui_list = ix.api.GuiListButton(panel, offset_x + 90, offset_y, 80, 22)
        default_selected_index = 0
        for color_space in color_spaces:
            gui_list.add_item(color_space)
            if color_space in options:
                default_selected_index = color_spaces.index(color_space)
        gui_list.set_selected_item_by_index(default_selected_index)
        color_space_list_buttons[key] = gui_list
        i += 1

    separator_label5 = ix.api.GuiLabel(panel, 10, 520, 380, 22, "[ OTHER OPTIONS ]")
    separator_label5.set_text_color(ix.api.GMathVec3uc(128, 128, 128))
    clip_opacity_label = ix.api.GuiLabel(panel, 10, 550, 150, 22,
                                         "Clip opacity: ")
    clip_opacity_checkbox = ix.api.GuiCheckbox(panel, 180, 550, "")

    lod_label = ix.api.GuiLabel(panel, 220, 550, 180, 22, "LOD: ")
    lod_types = ['High', '0', '1', '2', '3', '4', '5']
    lod_list = ix.api.GuiListButton(panel, 270, 550, 120, 22)
    for lod_type in lod_types:
        lod_list.add_item(lod_type)
    lod_list.set_selected_item_by_index(0)

    ior_label = ix.api.GuiLabel(panel, 10, 580, 150, 22, "IOR value:")
    ior_field = ix.api.GuiNumberField(panel, 145, 580, 50, "")
    ior_field.set_slider_range(1, 10)
    ior_field.set_increment(0.1)
    ior_field.enable_slider_range(True)
    metallic_ior_label = ix.api.GuiLabel(panel, 220, 580, 150, 22, "Metallic IOR value:")
    metallic_ior_field = ix.api.GuiNumberField(panel, 335, 580, 50, "")
    metallic_ior_field.set_slider_range(1, 10)
    metallic_ior_field.set_increment(0.1)
    metallic_ior_field.enable_slider_range(True)

    close_button = ix.api.GuiPushButton(panel, 10, 610, 100, 22, "Close")
    run_button = ix.api.GuiPushButton(panel, 130, 610, 250, 22, "Import")

    # init values
    triplanar_blend_field.set_value(0.5)
    ior_field.set_value(DEFAULT_IOR)
    metallic_ior_field.set_value(DEFAULT_METALLIC_IOR)

    clip_opacity_checkbox.set_value(True)

    # Connect to function
    event_rewire = EventRewire()  # init the class
    event_rewire.connect(color_space_presets_list, 'EVT_ID_LIST_BUTTON_SELECT',
                         event_rewire.color_space_preset_refresh)
    for key, color_space_list_button in color_space_list_buttons.iteritems():
        event_rewire.connect(color_space_list_button, 'EVT_ID_LIST_BUTTON_SELECT',
                             event_rewire.color_space_preset_refresh)
    event_rewire.connect(path_button, 'EVT_ID_PUSH_BUTTON_CLICK',
                         event_rewire.path_refresh)
    event_rewire.connect(close_button, 'EVT_ID_PUSH_BUTTON_CLICK',
                         event_rewire.cancel)
    event_rewire.connect(run_button, 'EVT_ID_PUSH_BUTTON_CLICK',
                         event_rewire.run)

    # Send all info to clarisse to generate window
    window.show()
    while window.is_shown():    ix.application.check_for_events()
    window.destroy()


def get_ix(ix_local):
    """Simple function to check if ix is imported or not."""
    try:
        ix
    except NameError:
        return ix_local
    else:
        return ix


import_asset_gui()
