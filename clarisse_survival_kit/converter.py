from clarisse_survival_kit.settings import *
from clarisse_survival_kit.app import *
import logging
import os


def get_selected_textures(items=None):
    textures = []
    if items is None:
        items = ix.selection
    for item in items:
        print(str(item))
        kind = ['TextureStreamedMapFile', 'TextureMapFile']
        if item.is_context():
            ctx_textures = get_items(item, kind=kind, ix=ix)
            textures = textures + get_selected_textures(ctx_textures)
        elif item.get_class_name() in kind:
            if str(item).endswith(PREVIEW_SUFFIX):
                continue
            textures.append(item)
    return textures


def converter_gui():
    logging.debug("Converter GUI started")

    class EventRewire(ix.api.EventObject):
        def path_refresh(self, sender, evtid):
            directory = ix.api.GuiWidget.open_folder(ix.application, '',
                                                     'Target directory')  # Summon the window to choose files
            if directory:
                if os.path.isdir(str(directory)):
                    path_txt.set_text(str(directory))
                else:
                    ix.log_warning("Invalid directory: %s" % str(directory))

        def add_selected(self, sender, evtid):
            textures = get_selected_textures()
            for tx in textures:
                if selection_list.find_item_by_name(str(tx)) == -1:
                    selection_list.add_item(str(tx))

        def remove_selected(self, sender, evtid):
            if selection_list.get_selected_index() >= 0:
                selection_list.remove_item(selection_list.get_selected_index())

        def cancel(self, sender, evtid):
            sender.get_window().hide()

        def run(self, sender, evtid):
            directory = path_txt.get_text()
            if directory and not os.path.isdir(str(directory)):
                ix.log_warning("No valid directory specified")
                return None
            ix.begin_command_batch("Convert")
            count = selection_list.get_item_count()
            progress = ix.application.create_progress_bar('Converting textures...')
            progress.set_value(0.0)
            progress.set_step_count(count)
            progress.start()
            for i in range(0, count):
                tx = ix.get_item(selection_list.get_item_name(i))
                if tx:
                    convert_tx(tx, extension=extension_list.get_selected_item_name(),
                               replace=replace_checkbox.get_value(), target_folder=directory, ix=ix)
                progress.step(i)
                ix.application.check_for_events()
            progress.destroy()
            ix.end_command_batch()

    # Window creation
    clarisse_win = ix.application.get_event_window()
    window = ix.api.GuiWindow(clarisse_win, 900, 450, 600, 380)  # Parent, X position, Y position, Width, Height
    window.set_title('Converter')  # Window name

    # Main widget creation
    panel = ix.api.GuiPanel(window, 0, 0, window.get_width(), window.get_height())
    panel.set_constraints(ix.api.GuiWidget.CONSTRAINT_LEFT, ix.api.GuiWidget.CONSTRAINT_TOP,
                          ix.api.GuiWidget.CONSTRAINT_RIGHT, ix.api.GuiWidget.CONSTRAINT_BOTTOM)

    # Form generation
    separator_label1 = ix.api.GuiLabel(panel, 10, 10, 380, 22, "[ TARGET DIRECTORY: (OPTIONAL) ]")
    separator_label1.set_text_color(ix.api.GMathVec3uc(128, 128, 128))
    path_button = ix.api.GuiPushButton(panel, 520, 40, 60, 22, "Browse")
    path_txt = ix.api.GuiLineEdit(panel, 10, 40, 500, 22)

    separator_label2 = ix.api.GuiLabel(panel, 10, 70, 580, 22, "[ SETTINGS: ]")
    separator_label2.set_text_color(ix.api.GMathVec3uc(128, 128, 128))

    extensions_label = ix.api.GuiLabel(panel, 10, 100, 150, 22, "Extension: ")
    extension_list = ix.api.GuiListButton(panel, 180, 100, 120, 22)
    for extension in [x for x in IMAGE_FORMATS if x != 'png']:
        extension_list.add_item(extension)
    extension_list.set_selected_item_by_index(0)

    replace_label = ix.api.GuiLabel(panel, 10, 130, 150, 22, "Replace textures: ")
    replace_checkbox = ix.api.GuiCheckbox(panel, 180, 130, "")
    replace_checkbox.set_value(True)

    selection_label = ix.api.GuiLabel(panel, 10, 160, 350, 22, "Textures that will be converted: ")
    textures = get_selected_textures()
    selection_list = ix.api.GuiListView(panel, 10, 180, 580, 90)
    for tx in textures:
        selection_list.add_item(str(tx))
    selection_list.set_mouse_over_selection(False)
    add_button = ix.api.GuiPushButton(panel, 10, 280, 450, 22, "Add selected")
    remove_button = ix.api.GuiPushButton(panel, 480, 280, 100, 22, "Remove")

    # progress_bar = ix.api.GuiProgressBar(panel, 10, 310, 580, 22)

    close_button = ix.api.GuiPushButton(panel, 10, 340, 100, 22, "Close")
    run_button = ix.api.GuiPushButton(panel, 330, 340, 250, 22, "Convert")


    # Connect to function
    event_rewire = EventRewire()  # init the class
    event_rewire.connect(add_button, 'EVT_ID_PUSH_BUTTON_CLICK',
                         event_rewire.add_selected)
    event_rewire.connect(remove_button, 'EVT_ID_PUSH_BUTTON_CLICK',
                         event_rewire.remove_selected)
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


converter_gui()
