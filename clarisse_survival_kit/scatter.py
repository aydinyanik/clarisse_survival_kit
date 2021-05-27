from clarisse_survival_kit.app import *
from clarisse_survival_kit.utility import check_selection


def generate_decimated_pointcloud_gui():
    class EventRewire(ix.api.EventObject):
        def pc_type(self, sender, evtid):
            if sender == pc_checkbox:
                pc_checkbox.set_value(True)
                pc_uv_checkbox.set_value(False)
            else:
                pc_uv_checkbox.set_value(True)
                pc_checkbox.set_value(False)
                use_density_checkbox.set_value(False)

        def use_density(self, sender, evtid):
            if pc_uv_checkbox.get_value() and use_density_checkbox.get_value():
                pc_uv_checkbox.set_value(False)
                pc_checkbox.set_value(True)

        def cancel(self, sender, evtid):
            sender.get_window().hide()

        def run(self, sender, evtid):
            geometry = None
            if ix.selection.get_count() > 0 and check_selection([ix.selection[0]], is_kindof=["Geometry", "SceneObjectCombiner"], max_num=1):
                geometry = ix.selection[0]
            else:
                ix.log_warning("Please select an object to scatter on.")
                return False
            pc_type = "GeometryPointCloud" if pc_checkbox.get_value() else "GeometryPointUvSampler"
            ix.begin_command_batch("Scatter pointcloud")
            pc = generate_decimated_pointcloud(geometry, pc_type=pc_type,
                                               use_density=use_density_checkbox.get_value(),
                                               density=density_field.get_value(),
                                               point_count=point_count_field.get_value(),
                                               slope_blend=slope_blend_checkbox.get_value(),
                                               scope_blend=scope_blend_checkbox.get_value(),
                                               height_blend=height_blend_checkbox.get_value(),
                                               fractal_blend=fractal_blend_checkbox.get_value(),
                                               triplanar_blend=triplanar_blend_checkbox.get_value(),
                                               ao_blend=ao_blend_checkbox.get_value(), ix=ix)
            if pc:
                ix.application.check_for_events()
                ix.selection.deselect_all()
                ix.selection.add(pc)
                ix.end_command_batch()
                sender.get_window().hide()
            else:
                ix.end_command_batch()

    # Window creation
    clarisse_win = ix.application.get_event_window()
    window = ix.api.GuiWindow(clarisse_win, 900, 450, 400, 370)  # Parent, X position, Y position, Width, Height
    window.set_title('Scatter Point Cloud on Geometry')  # Window name

    # Main widget creation
    panel = ix.api.GuiPanel(window, 0, 0, window.get_width(), window.get_height())
    panel.set_constraints(ix.api.GuiWidget.CONSTRAINT_LEFT, ix.api.GuiWidget.CONSTRAINT_TOP,
                          ix.api.GuiWidget.CONSTRAINT_RIGHT, ix.api.GuiWidget.CONSTRAINT_BOTTOM)

    # Form generation
    pc_label = ix.api.GuiLabel(panel, 10, 10, 150, 22,
                               "Point Cloud: ")
    pc_checkbox = ix.api.GuiCheckbox(panel, 180, 10, "")
    pc_uv_label = ix.api.GuiLabel(panel, 220, 10, 150, 22,
                                  "Point UV Sampler: ")
    pc_uv_checkbox = ix.api.GuiCheckbox(panel, 370, 10, "")
    use_density_label = ix.api.GuiLabel(panel, 10, 40, 150, 22,
                                        "Use density: ")
    use_density_checkbox = ix.api.GuiCheckbox(panel, 180, 40, "")
    density_field = ix.api.GuiNumberField(panel, 267, 40, 100, "Density:")
    density_field.set_slider_range(0, 200)
    density_field.set_increment(0.005)
    density_field.enable_slider_range(True)
    point_count_field = ix.api.GuiNumberField(panel, 80, 70, 200, "Point count:")
    point_count_field.set_slider_range(0, 10000000)
    point_count_field.set_increment(100)
    point_count_field.enable_slider_range(True)

    fractal_blend_label = ix.api.GuiLabel(panel, 10, 130, 150, 22,
                                          "Fractal blend: ")
    fractal_blend_checkbox = ix.api.GuiCheckbox(panel, 205, 130, "")
    triplanar_blend_label = ix.api.GuiLabel(panel, 10, 160, 150, 22,
                                            "Triplanar blend: ")
    triplanar_blend_checkbox = ix.api.GuiCheckbox(panel, 205, 160, "")
    slope_blend_label = ix.api.GuiLabel(panel, 10, 190, 150, 22,
                                        "Slope blend: ")
    slope_blend_checkbox = ix.api.GuiCheckbox(panel, 205, 190, "")
    scope_blend_label = ix.api.GuiLabel(panel, 10, 220, 150, 22,
                                        "Scope blend: ")
    scope_blend_checkbox = ix.api.GuiCheckbox(panel, 205, 220, "")
    ao_blend_label = ix.api.GuiLabel(panel, 10, 250, 150, 22,
                                     "Occlusion blend: ")
    ao_blend_checkbox = ix.api.GuiCheckbox(panel, 205, 250, "")
    height_blend_label = ix.api.GuiLabel(panel, 10, 280, 190, 22,
                                         "Height blend: ")
    height_blend_checkbox = ix.api.GuiCheckbox(panel, 205, 280, "")

    cancel_btn = ix.api.GuiPushButton(panel, 10, 330, 100, 22, "Close")  # The cancel button (destroy the script window)
    run_btn = ix.api.GuiPushButton(panel, 130, 330, 250, 22, "Apply")  # The run button to run your script

    # init values
    pc_checkbox.set_value(True)
    use_density_checkbox.set_value(True)
    density_field.set_value(0.1)
    point_count_field.set_value(100000)
    slope_blend_checkbox.set_value(True)
    fractal_blend_checkbox.set_value(True)

    # Connect to function
    event_rewire = EventRewire()  # init the class
    event_rewire.connect(pc_checkbox, 'EVT_ID_CHECKBOX_CLICK', event_rewire.pc_type)
    event_rewire.connect(pc_uv_checkbox, 'EVT_ID_CHECKBOX_CLICK', event_rewire.pc_type)
    event_rewire.connect(use_density_checkbox, 'EVT_ID_CHECKBOX_CLICK', event_rewire.use_density)
    event_rewire.connect(cancel_btn, 'EVT_ID_PUSH_BUTTON_CLICK', event_rewire.cancel)
    event_rewire.connect(run_btn, 'EVT_ID_PUSH_BUTTON_CLICK', event_rewire.run)

    # Send all info to clarisse to generate window
    window.show()
    while window.is_shown():    ix.application.check_for_events()
    window.destroy()


generate_decimated_pointcloud_gui()
