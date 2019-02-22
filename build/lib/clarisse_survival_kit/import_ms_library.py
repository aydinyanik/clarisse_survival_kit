from clarisse_survival_kit.app import *
from clarisse_survival_kit.providers.megascans import import_ms_library


def import_ms_library_gui():
    skip_categories = []

    class EventRewire(ix.api.EventObject):
        def categories_refresh(self, sender, evtid):
            for key, category_checkbox in category_checkboxes.iteritems():
                if not category_checkbox.get_value():
                    skip_categories.append(key)
                else:
                    if key in skip_categories:
                        skip_categories.pop(skip_categories.index(key))

        def path_refresh(self, sender, evtid):
            directory = ix.api.GuiWidget.open_folder(ix.application, '',
                                                     'Library directory')  # Summon the window to choose files
            if directory:
                if os.path.isdir(str(directory)):
                    path_txt.set_text(str(directory))
                else:
                    ix.log_warning("Invalid directory: %s" % str(directory))

        def cancel(self, sender, evtid):
            sender.get_window().hide()

        def run(self, sender, evtid):
            ix.begin_command_batch("Import Megascans library")
            resolution = resolution_list.get_selected_item_name()
            if resolution == 'Auto':
                resolution = None
            lod = lod_list.get_selected_item_name()
            if lod == 'High':
                lod = -1
            else:
                lod = int(lod)
            directory = path_txt.get_text()
            if directory:
                if os.path.isdir(directory):
                    import_ms_library(directory, target_ctx=None, custom_assets=cat_custom_checkbox.get_value(),
                                      skip_categories=skip_categories, lod=lod, resolution=resolution, ix=ix)
                    ix.application.check_for_events()
                else:
                    ix.log_warning("Invalid directory: %s" % directory)
            else:
                ix.log_warning("No directory specified")
            ix.end_command_batch()

    # Window creation
    clarisse_win = ix.application.get_event_window()
    window = ix.api.GuiWindow(clarisse_win, 900, 450, 400, 380)  # Parent, X position, Y position, Width, Height
    window.set_title('Import Megascans library')  # Window name

    # Main widget creation
    panel = ix.api.GuiPanel(window, 0, 0, window.get_width(), window.get_height())
    panel.set_constraints(ix.api.GuiWidget.CONSTRAINT_LEFT, ix.api.GuiWidget.CONSTRAINT_TOP,
                          ix.api.GuiWidget.CONSTRAINT_RIGHT, ix.api.GuiWidget.CONSTRAINT_BOTTOM)

    # Form generation
    separator_label1 = ix.api.GuiLabel(panel, 10, 10, 380, 22, "[ MEGASCANS LIBRARY PATH ]")
    separator_label1.set_text_color(ix.api.GMathVec3uc(128, 128, 128))
    path_button = ix.api.GuiPushButton(panel, 320, 40, 60, 22, "Browse")
    path_txt = ix.api.GuiLineEdit(panel, 10, 40, 300, 22)
    separator_label2 = ix.api.GuiLabel(panel, 10, 100, 380, 22, "[ CATEGORIES ]")
    separator_label2.set_text_color(ix.api.GMathVec3uc(128, 128, 128))
    cat_3d_label = ix.api.GuiLabel(panel, 10, 130, 100, 22,
                                   "3D:")
    cat_3d_checkbox = ix.api.GuiCheckbox(panel, 180, 130, "")
    cat_3dplant_label = ix.api.GuiLabel(panel, 220, 130, 100, 22,
                                        "3D Plant:")
    cat_3dplant_checkbox = ix.api.GuiCheckbox(panel, 370, 130, "")
    cat_atlas_label = ix.api.GuiLabel(panel, 10, 160, 100, 22,
                                      "Atlas:")
    cat_atlas_checkbox = ix.api.GuiCheckbox(panel, 180, 160, "")
    cat_surface_label = ix.api.GuiLabel(panel, 220, 160, 100, 22,
                                        "Surface:")
    cat_surface_checkbox = ix.api.GuiCheckbox(panel, 370, 160, "")
    cat_custom_label = ix.api.GuiLabel(panel, 10, 190, 100, 22, "Custom Assets:")
    cat_custom_checkbox = ix.api.GuiCheckbox(panel, 180, 190, "")

    separator_label3 = ix.api.GuiLabel(panel, 10, 220, 380, 22, "[ OPTIONS ]")
    separator_label3.set_text_color(ix.api.GMathVec3uc(128, 128, 128))

    lod_label = ix.api.GuiLabel(panel, 10, 250, 180, 22, "LOD: ")
    lod_types = ['High', '0', '1', '2', '3', '4', '5']
    lod_list = ix.api.GuiListButton(panel, 180, 250, 120, 22)
    for lod_type in lod_types:
        lod_list.add_item(lod_type)
    lod_list.set_selected_item_by_index(0)

    resolution_label = ix.api.GuiLabel(panel, 10, 280, 180, 22, "Resolution: ")
    resolution_types = ['Auto'] + IMAGE_RESOLUTIONS
    resolution_list = ix.api.GuiListButton(panel, 180, 280, 120, 22)
    for resolution_type in resolution_types:
        resolution_list.add_item(resolution_type)
    resolution_list.set_selected_item_by_index(0)

    category_checkboxes = {
        '3d': cat_3d_checkbox,
        '3dplant': cat_3dplant_checkbox,
        'atlas': cat_atlas_checkbox,
        'surface': cat_surface_checkbox,
    }

    close_button = ix.api.GuiPushButton(panel, 10, 330, 100, 22, "Close")
    run_button = ix.api.GuiPushButton(panel, 130, 330, 250, 22, "Import")

    # init values
    cat_3d_checkbox.set_value(True)
    cat_3dplant_checkbox.set_value(True)
    cat_atlas_checkbox.set_value(True)
    cat_surface_checkbox.set_value(True)
    cat_custom_checkbox.set_value(True)

    # Connect to function
    event_rewire = EventRewire()  # init the class

    for key, category_checkbox in category_checkboxes.iteritems():
        event_rewire.connect(category_checkbox, 'EVT_ID_CHECKBOX_CLICK',
                             event_rewire.categories_refresh)
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


import_ms_library_gui()
