from clarisse_survival_kit.settings import *
from clarisse_survival_kit.app import *


def import_asset_gui(**kwargs):
    ix = get_ix(kwargs.get('ix'))
    result = {'object_space': 0}

    class EventRewire(ix.api.EventObject):
        def mapping_refresh(self, sender, evtid):
            for index, checkbox in mapping_checkboxes.iteritems():
                checkbox.set_value(checkbox == sender)

        def os_base_refresh(self, sender, evtid):
            result['object_space'] = 0
            os_world_checkbox.set_value(False)
            os_base_checkbox.set_value(True)

        def os_world_refresh(self, sender, evtid):
            result['object_space'] = 2
            os_world_checkbox.set_value(True)
            os_base_checkbox.set_value(False)

        def color_space_preset(self, sender, evtid):
            if sender == megascans_srgb_checkbox:
                megascans_srgb_checkbox.set_value(True)
                substance_srgb_checkbox.set_value(False)
                for index, checkbox in color_space_checkboxes.iteritems():
                    checkbox.set_value(index in MEGASCANS_SRGB_TEXTURES)
            elif sender == substance_srgb_checkbox:
                substance_srgb_checkbox.set_value(True)
                megascans_srgb_checkbox.set_value(False)
                for index, checkbox in color_space_checkboxes.iteritems():
                    checkbox.set_value(index in SUBSTANCE_SRGB_TEXTURES)
            else:
                srgb = []
                for index, checkbox in color_space_checkboxes.iteritems():
                    if checkbox.get_value():
                        srgb.append(index)
                if set(srgb) == set(MEGASCANS_SRGB_TEXTURES):
                    megascans_srgb_checkbox.set_value(True)
                    substance_srgb_checkbox.set_value(False)
                elif set(srgb) == set(SUBSTANCE_SRGB_TEXTURES):
                    print list(set(srgb).intersection(set(SUBSTANCE_SRGB_TEXTURES)))
                    megascans_srgb_checkbox.set_value(False)
                    substance_srgb_checkbox.set_value(True)
                else:
                    megascans_srgb_checkbox.set_value(False)
                    substance_srgb_checkbox.set_value(False)

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
                        srgb = []
                        for index, checkbox in color_space_checkboxes.iteritems():
                            if checkbox.get_value():
                                srgb.append(index)
                        mapping = None
                        for index, checkbox in mapping_checkboxes.iteritems():
                            if checkbox.get_value():
                                mapping = index
                        surface = import_asset(directory,
                                               projection_type=mapping,
                                               clip_opacity=clip_opacity_checkbox.get_value(),
                                               object_space=result['object_space'],
                                               srgb=srgb,
                                               triplanar_blend=triplanar_blend_field.get_value(),
                                               ior=ior_field.get_value(),
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
    separator_label1 = ix.api.GuiLabel(panel, 10, 10, 380, 22, "[ ASSET PATH ]")
    separator_label1.set_text_color(ix.api.GMathVec3uc(128, 128, 128))
    path_button = ix.api.GuiPushButton(panel, 320, 40, 60, 22, "Browse")
    path_txt = ix.api.GuiLineEdit(panel, 10, 40, 300, 22)
    separator_label2 = ix.api.GuiLabel(panel, 10, 100, 380, 22, "[ MAPPING ]")
    separator_label2.set_text_color(ix.api.GMathVec3uc(128, 128, 128))
    uv_label = ix.api.GuiLabel(panel, 10, 130, 100, 22,
                               "UV:")
    uv_checkbox = ix.api.GuiCheckbox(panel, 180, 130, "")
    cubic_label = ix.api.GuiLabel(panel, 220, 130, 100, 22,
                                  "Cubic:")
    cubic_checkbox = ix.api.GuiCheckbox(panel, 370, 130, "")
    # triplanar_label = ix.api.GuiLabel(panel, 10, 160, 150, 22,
    #                                          "Triplanar:")
    triplanar_blend_field = ix.api.GuiNumberField(panel, 97, 160, 50, "Triplanar Blend:")
    triplanar_blend_field.set_slider_range(0, 1)
    triplanar_blend_field.set_increment(0.1)
    triplanar_blend_field.enable_slider_range(True)

    triplanar_checkbox = ix.api.GuiCheckbox(panel, 180, 160, "")
    spherical_label = ix.api.GuiLabel(panel, 220, 160, 100, 22,
                                      "Spherical:")
    spherical_checkbox = ix.api.GuiCheckbox(panel, 370, 160, "")
    planar_label = ix.api.GuiLabel(panel, 10, 190, 150, 22,
                                   "Planar (Y):")
    planar_checkbox = ix.api.GuiCheckbox(panel, 180, 190, "")
    cylindrical_label = ix.api.GuiLabel(panel, 220, 190, 150, 22,
                                        "Cylindrical:")
    cylindrical_checkbox = ix.api.GuiCheckbox(panel, 370, 190, "")

    mapping_checkboxes = {
        'uv': uv_checkbox,
        'triplanar': triplanar_checkbox,
        'cubic': cubic_checkbox,
        'spherical': spherical_checkbox,
        'planar': planar_checkbox,
        'cylindrical': cylindrical_checkbox
    }

    os_base_label = ix.api.GuiLabel(panel, 10, 220, 150, 22,
                                    "Object Space (Base): ")
    os_base_checkbox = ix.api.GuiCheckbox(panel, 180, 220, "")
    os_world_label = ix.api.GuiLabel(panel, 220, 220, 150, 22,
                                     "Object Space (World): ")
    os_world_checkbox = ix.api.GuiCheckbox(panel, 370, 220, "")
    separator_label3 = ix.api.GuiLabel(panel, 10, 280, 380, 22, "[ COLOR SPACE: sRGB ]")
    separator_label3.set_text_color(ix.api.GMathVec3uc(128, 128, 128))

    megascans_label = ix.api.GuiLabel(panel, 190, 280, 150, 22,
                                      "Megascans:")
    megascans_srgb_checkbox = ix.api.GuiCheckbox(panel, 260, 280, "")
    substance_label = ix.api.GuiLabel(panel, 300, 280, 150, 22,
                                      "Substance:")
    substance_srgb_checkbox = ix.api.GuiCheckbox(panel, 370, 280, "")

    diffuse_srgb_label = ix.api.GuiLabel(panel, 10, 310, 150, 22,
                                         "Diffuse: ")
    diffuse_srgb_checkbox = ix.api.GuiCheckbox(panel, 180, 310, "")
    specular_srgb_label = ix.api.GuiLabel(panel, 220, 310, 150, 22,
                                          "Specular: ")
    specular_srgb_checkbox = ix.api.GuiCheckbox(panel, 370, 310, "")

    roughness_srgb_label = ix.api.GuiLabel(panel, 10, 340, 150, 22,
                                           "Roughness: ")
    roughness_srgb_checkbox = ix.api.GuiCheckbox(panel, 180, 340, "")
    normal_srgb_label = ix.api.GuiLabel(panel, 220, 340, 150, 22,
                                        "Normal: ")
    normal_srgb_checkbox = ix.api.GuiCheckbox(panel, 370, 340, "")

    displacement_srgb_label = ix.api.GuiLabel(panel, 10, 370, 150, 22,
                                              "Displacement: ")
    displacement_srgb_checkbox = ix.api.GuiCheckbox(panel, 180, 370, "")
    bump_srgb_label = ix.api.GuiLabel(panel, 220, 370, 150, 22,
                                      "Bump: ")
    bump_srgb_checkbox = ix.api.GuiCheckbox(panel, 370, 370, "")

    emissive_srgb_label = ix.api.GuiLabel(panel, 10, 400, 150, 22,
                                          "Emissive: ")
    emissive_srgb_checkbox = ix.api.GuiCheckbox(panel, 180, 400, "")
    ior_srgb_label = ix.api.GuiLabel(panel, 220, 400, 150, 22,
                                     "IOR: ")
    ior_srgb_checkbox = ix.api.GuiCheckbox(panel, 370, 400, "")

    opacity_srgb_label = ix.api.GuiLabel(panel, 10, 430, 150, 22,
                                         "Opacity: ")
    opacity_srgb_checkbox = ix.api.GuiCheckbox(panel, 180, 430, "")
    translucency_srgb_label = ix.api.GuiLabel(panel, 220, 430, 150, 22,
                                              "Translucency: ")
    translucency_srgb_checkbox = ix.api.GuiCheckbox(panel, 370, 430, "")

    refraction_srgb_label = ix.api.GuiLabel(panel, 10, 460, 150, 22,
                                            "Refraction: ")
    refraction_srgb_checkbox = ix.api.GuiCheckbox(panel, 180, 460, "")

    color_space_checkboxes = {
        'diffuse': diffuse_srgb_checkbox,
        'specular': specular_srgb_checkbox,
        'roughness': roughness_srgb_checkbox,
        'normal': normal_srgb_checkbox,
        'displacement': displacement_srgb_checkbox,
        'bump': bump_srgb_checkbox,
        'emissive': emissive_srgb_checkbox,
        'ior': ior_srgb_checkbox,
        'refraction': refraction_srgb_checkbox,
        'translucency': translucency_srgb_checkbox,
        'opacity': opacity_srgb_checkbox
    }

    separator_label4 = ix.api.GuiLabel(panel, 10, 520, 380, 22, "[ OTHER OPTIONS ]")
    separator_label4.set_text_color(ix.api.GMathVec3uc(128, 128, 128))
    clip_opacity_label = ix.api.GuiLabel(panel, 10, 550, 150, 22,
                                         "Clip opacity: ")
    clip_opacity_checkbox = ix.api.GuiCheckbox(panel, 180, 550, "")
    ior_field = ix.api.GuiNumberField(panel, 280, 550, 50, "IOR value:")
    ior_field.set_slider_range(1, 10)
    ior_field.set_increment(0.1)
    ior_field.enable_slider_range(True)

    close_button = ix.api.GuiPushButton(panel, 10, 610, 100, 22, "Close")
    run_button = ix.api.GuiPushButton(panel, 130, 610, 250, 22, "Import")

    # init values
    triplanar_checkbox.set_value(True)
    triplanar_blend_field.set_value(0.5)
    ior_field.set_value(DEFAULT_IOR)

    clip_opacity_checkbox.set_value(True)
    os_base_checkbox.set_value(True)

    megascans_srgb_checkbox.set_value(True)

    # Connect to function
    event_rewire = EventRewire()  # init the class

    event_rewire.connect(os_base_checkbox, 'EVT_ID_CHECKBOX_CLICK',
                         event_rewire.os_base_refresh)
    event_rewire.connect(os_world_checkbox, 'EVT_ID_CHECKBOX_CLICK',
                         event_rewire.os_world_refresh)
    for key, mapping_checkbox in mapping_checkboxes.iteritems():
        event_rewire.connect(mapping_checkbox, 'EVT_ID_CHECKBOX_CLICK',
                             event_rewire.mapping_refresh)

    for key, color_space_checkbox in color_space_checkboxes.iteritems():
        if key in MEGASCANS_SRGB_TEXTURES:
            color_space_checkbox.set_value(True)
        event_rewire.connect(color_space_checkbox, 'EVT_ID_CHECKBOX_CLICK',
                             event_rewire.color_space_preset)
    event_rewire.connect(megascans_srgb_checkbox, 'EVT_ID_CHECKBOX_CLICK',
                         event_rewire.color_space_preset)
    event_rewire.connect(substance_srgb_checkbox, 'EVT_ID_CHECKBOX_CLICK',
                         event_rewire.color_space_preset)
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
