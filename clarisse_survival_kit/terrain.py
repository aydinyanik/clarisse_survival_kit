from clarisse_survival_kit.app import *


def terrain_gui(heightmap=''):
    class EventRewire(ix.api.EventObject):
        def toggle_uniform_scale(self, sender, evtid):
            if sender.get_value():
                length_field.disable()
                tiles_y_field.disable()
            else:
                length_field.enable()
                tiles_y_field.enable()

        def set_dimensions(self, sender, evtid):
            if uniform_scale_checkbox.get_value():
                length_field.set_value(sender.get_value())

        def set_tiles(self, sender, evtid):
            if uniform_scale_checkbox.get_value():
                tiles_y_field.set_value(sender.get_value())

        def path_refresh(self, sender, evtid):
            heightmap_file = ix.api.GuiWidget.open_file(ix.application, '',
                                                        'Heightmap file')  # Summon the window to choose files
            if heightmap_file:
                if os.path.isfile(str(heightmap_file)):
                    filename, ext = os.path.splitext(heightmap_file)
                    if ext.lstrip('.').lower() not in IMAGE_FORMATS:
                        ix.log_warning("Invalid file: %s" % str(heightmap_file))
                        return None
                    path_txt.set_text(str(heightmap_file))
                else:
                    ix.log_warning("Invalid file: %s" % str(heightmap_file))

        def cancel(self, sender, evtid):
            sender.get_window().hide()

        def run(self, sender, evtid):
            ix.begin_command_batch("Setup terrain")
            heightmap_file = path_txt.get_text()
            dimensions = (int(width_field.get_value()),
                          int(length_field.get_value()),
                          int(height_field.get_value()),
                          )
            adaptive_spans = int(adaptive_spans_list.get_selected_item_name())
            spans = int(spans_list.get_selected_item_name())
            repeat = repeat_list.get_selected_item_name().lower()
            proxy_adaptive_spans = int((1 / float(
                proxy_adaptive_spans_quality_list.get_selected_item_name().split("/")[1])) * adaptive_spans)
            proxy_spans = int((1 / float(proxy_spans_quality_list.get_selected_item_name().split("/")[1])) * spans)
            if heightmap_file:
                if os.path.isfile(heightmap_file):
                    tile_pattern = r"{}".format(tile_regex_txt.get_text())
                    tile_match = re.search(tile_pattern, r"{}".format(heightmap_file), re.IGNORECASE)
                    if (int(tiles_x_field.get_value()) > 1 or int(tiles_y_field.get_value()) > 1) or tile_match:
                        terrain = create_tiled_terrain(heightmap_file=heightmap_file,
                                                       terrain_name=name_txt.get_text(),
                                                       dimensions=dimensions,
                                                       divisions_x=int(tiles_x_field.get_value()),
                                                       divisions_y=int(tiles_y_field.get_value()),
                                                       stream=stream_checkbox.get_value(),
                                                       adaptive_spans=adaptive_spans,
                                                       spans=spans,
                                                       animated=animated_checkbox.get_value(),
                                                       generate_proxy=proxy_checkbox.get_value(),
                                                       proxy_adaptive_spans=proxy_adaptive_spans,
                                                       proxy_spans=proxy_spans,
                                                       repeat=repeat, use_midpoint=midpoint_checkbox.get_value(),
                                                       tile_flip_x=tile_flip_x_checkbox.get_value(),
                                                       tile_flip_y=tile_flip_y_checkbox.get_value(),
                                                       tile_pattern=tile_pattern,
                                                       displacement_mode=int(displacement_mode_list.get_selected_item_index()),
                                                       ix=ix)
                    else:
                        terrain = create_terrain(heightmap_file, name_txt.get_text(), dimensions=dimensions,
                                                 stream=stream_checkbox.get_value(),
                                                 adaptive_spans=adaptive_spans,
                                                 spans=spans,
                                                 animated=animated_checkbox.get_value(),
                                                 generate_proxy=proxy_checkbox.get_value(),
                                                 proxy_adaptive_spans=proxy_adaptive_spans,
                                                 proxy_spans=proxy_spans,
                                                 displacement_mode=int(displacement_mode_list.get_selected_item_index()),
                                                 repeat=repeat, use_midpoint=midpoint_checkbox.get_value(),
                                                 ix=ix)
                    if terrain:
                        ix.selection.deselect_all()
                        ix.selection.add(terrain)
                    ix.application.check_for_events()
                else:
                    ix.log_warning("Invalid file: %s" % heightmap_file)
            else:
                ix.log_warning("No heightmap file specified")
            ix.end_command_batch()

    # Window creation
    clarisse_win = ix.application.get_event_window()
    window = ix.api.GuiWindow(clarisse_win, 900, 450, 400, 640)  # Parent, X position, Y position, Width, Height
    window.set_title('Heightmap wizard')  # Window name

    # Main widget creation
    panel = ix.api.GuiPanel(window, 0, 0, window.get_width(), window.get_height())
    panel.set_constraints(ix.api.GuiWidget.CONSTRAINT_LEFT, ix.api.GuiWidget.CONSTRAINT_TOP,
                          ix.api.GuiWidget.CONSTRAINT_RIGHT, ix.api.GuiWidget.CONSTRAINT_BOTTOM)

    # Form generation
    separator_label1 = ix.api.GuiLabel(panel, 10, 10, 380, 22, "[ HEIGHTMAP ]")
    separator_label1.set_text_color(ix.api.GMathVec3uc(128, 128, 128))
    path_button = ix.api.GuiPushButton(panel, 320, 40, 60, 22, "Browse")
    path_txt = ix.api.GuiLineEdit(panel, 10, 40, 300, 22)
    if heightmap and os.path.isfile(heightmap):
        path_txt.set_text(heightmap)
    separator_label2 = ix.api.GuiLabel(panel, 10, 70, 380, 22, "[ SETTINGS ]")
    separator_label2.set_text_color(ix.api.GMathVec3uc(128, 128, 128))
    name_label = ix.api.GuiLabel(panel, 10, 100, 100, 22, "Name:")
    name_txt = ix.api.GuiLineEdit(panel, 150, 100, 230, 22)
    name_txt.set_text('terrain')

    uniform_scale_label = ix.api.GuiLabel(panel, 10, 130, 100, 22, "Uniform Scale:")
    uniform_scale_checkbox = ix.api.GuiCheckbox(panel, 140, 130, "")
    uniform_scale_checkbox.set_value(True)

    midpoint_label = ix.api.GuiLabel(panel, 200, 130, 100, 22, "Midpoint:")
    midpoint_checkbox = ix.api.GuiCheckbox(panel, 360, 130, "")

    width_label = ix.api.GuiLabel(panel, 10, 160, 100, 22, "Width:")
    length_label = ix.api.GuiLabel(panel, 150, 160, 100, 22, "Length:")
    height_label = ix.api.GuiLabel(panel, 290, 160, 100, 22, "Height:")
    width_field = ix.api.GuiNumberField(panel, 10, 190, 80, "")
    width_field.set_value(2048)
    length_field = ix.api.GuiNumberField(panel, 150, 190, 80, "")
    length_field.set_value(2048)
    length_field.disable()
    height_field = ix.api.GuiNumberField(panel, 290, 190, 80, "")
    height_field.set_value(400)

    adaptive_spans_label = ix.api.GuiLabel(panel, 10, 220, 150, 22,
                                           "Adaptive Span Count:")
    adaptive_spans_choices = ['16384', '8192', '4096', '2048', '1024', '512']
    adaptive_spans_list = ix.api.GuiListButton(panel, 260, 220, 120, 22)
    for adaptive_spans_type in adaptive_spans_choices:
        adaptive_spans_list.add_item(adaptive_spans_type)
    adaptive_spans_list.set_selected_item_by_index(2)

    spans_label = ix.api.GuiLabel(panel, 10, 250, 150, 22,
                                  "Span Count:")
    spans_choices = ['2048', '1024', '512', '256', '128', '64']
    spans_list = ix.api.GuiListButton(panel, 260, 250, 120, 22)
    for spans_type in spans_choices:
        spans_list.add_item(spans_type)
    spans_list.set_selected_item_by_index(2)

    proxy_label = ix.api.GuiLabel(panel, 10, 280, 150, 22, "Generate Proxy:")
    proxy_checkbox = ix.api.GuiCheckbox(panel, 140, 280, "")
    proxy_checkbox.set_value(True)

    proxy_adaptive_spans_quality_label = ix.api.GuiLabel(panel, 10, 310, 200, 22, "Proxy Adaptive Spans Multiplier:")
    proxy_adaptive_spans_quality_choices = ['1/2', '1/4', '1/8', '1/16']
    proxy_adaptive_spans_quality_list = ix.api.GuiListButton(panel, 260, 310, 120, 22)
    for proxy_adaptive_spans_quality_type in proxy_adaptive_spans_quality_choices:
        proxy_adaptive_spans_quality_list.add_item(proxy_adaptive_spans_quality_type)
    proxy_adaptive_spans_quality_list.set_selected_item_by_index(2)

    proxy_spans_quality_label = ix.api.GuiLabel(panel, 10, 340, 150, 22, "Proxy Span Multiplier:")
    proxy_spans_quality_choices = ['1', '1/2', '1/4', '1/8', '1/16']
    proxy_spans_quality_list = ix.api.GuiListButton(panel, 260, 340, 120, 22)
    for proxy_spans_quality_type in proxy_spans_quality_choices:
        proxy_spans_quality_list.add_item(proxy_spans_quality_type)
    proxy_spans_quality_list.set_selected_item_by_index(1)

    stream_label = ix.api.GuiLabel(panel, 10, 370, 100, 22, "Stream:")
    stream_checkbox = ix.api.GuiCheckbox(panel, 140, 370, "")
    stream_checkbox.set_value(False)

    animated_label = ix.api.GuiLabel(panel, 200, 370, 100, 22, "Animated:")
    animated_checkbox = ix.api.GuiCheckbox(panel, 360, 370, "")

    repeat_label = ix.api.GuiLabel(panel, 10, 400, 150, 22,
                                   "Repeat mode:")
    repeat_choices = ['Edge', 'Repeat']
    repeat_list = ix.api.GuiListButton(panel, 260, 400, 120, 22)
    for repeat_type in repeat_choices:
        repeat_list.add_item(repeat_type)
    repeat_list.set_selected_item_by_index(0)
    

    displacement_mode_label = ix.api.GuiLabel(panel, 10, 430, 150, 22,
                                   "Displacement Mode:")
    displacement_mode_choices = ['Heightmap', 'Vector (Tangent)', 'Vector (Object)']
    displacement_mode_list = ix.api.GuiListButton(panel, 260, 430, 120, 22)
    for displacement_mode_type in displacement_mode_choices:
        displacement_mode_list.add_item(displacement_mode_type)
    displacement_mode_list.set_selected_item_by_index(0)

    separator_label3 = ix.api.GuiLabel(panel, 10, 460, 380, 22, "[ TILING ]")
    separator_label3.set_text_color(ix.api.GMathVec3uc(128, 128, 128))

    tiles_x_label = ix.api.GuiLabel(panel, 10, 490, 100, 22, "Tiles (X):")
    tiles_x_field = ix.api.GuiNumberField(panel, 100, 490, 80, "")
    tiles_x_field.set_increment(1)
    tiles_x_field.set_slider_range(1, 128)
    tiles_x_field.enable_slider_range(True)
    tiles_x_field.set_value(1)

    tiles_y_label = ix.api.GuiLabel(panel, 200, 490, 100, 22, "Tiles (Y):")
    tiles_y_field = ix.api.GuiNumberField(panel, 300, 490, 80, "")
    tiles_y_field.set_increment(1)
    tiles_y_field.set_value(1)
    tiles_y_field.set_slider_range(1, 128)
    tiles_y_field.enable_slider_range(True)
    tiles_y_field.disable()

    tile_flip_x_label = ix.api.GuiLabel(panel, 10, 520, 100, 22, "Flip (X):")
    tile_flip_x_checkbox = ix.api.GuiCheckbox(panel, 140, 520, "")

    tile_flip_y_label = ix.api.GuiLabel(panel, 200, 520, 100, 22, "Flip (Y):")
    tile_flip_y_checkbox = ix.api.GuiCheckbox(panel, 360, 520, "")

    tile_regex_label = ix.api.GuiLabel(panel, 10, 550, 100, 22, "Auto Tile Regex:")
    tile_regex_txt = ix.api.GuiLineEdit(panel, 150, 550, 230, 22)
    tile_regex_txt.set_text(".*_x(?P<tile_x>\d+)_y(?P<tile_y>\d+)\.")

    close_button = ix.api.GuiPushButton(panel, 10, 610, 100, 22, "Close")
    run_button = ix.api.GuiPushButton(panel, 130, 610, 250, 22, "Import")

    # Connect to function
    event_rewire = EventRewire()  # init the class

    event_rewire.connect(uniform_scale_checkbox, 'EVT_ID_CHECKBOX_CLICK',
                         event_rewire.toggle_uniform_scale)
    event_rewire.connect(width_field, 'EVT_ID_NUMBER_FIELD_VALUE_CHANGED',
                         event_rewire.set_dimensions)
    event_rewire.connect(tiles_x_field, 'EVT_ID_NUMBER_FIELD_VALUE_CHANGED',
                         event_rewire.set_tiles)
    event_rewire.connect(path_button, 'EVT_ID_PUSH_BUTTON_CLICK',
                         event_rewire.path_refresh)
    event_rewire.connect(close_button, 'EVT_ID_PUSH_BUTTON_CLICK',
                         event_rewire.cancel)
    event_rewire.connect(run_button, 'EVT_ID_PUSH_BUTTON_CLICK',
                         event_rewire.run)

    # Send all info to clarisse to generate window
    window.show()
    while window.is_shown():
        ix.application.check_for_events()
    window.destroy()


terrain_gui()
