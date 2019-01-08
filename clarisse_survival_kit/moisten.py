from clarisse_survival_kit.settings import *
from clarisse_survival_kit.app import *


def moisten_surface_gui():
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
			ix.begin_command_batch("Moisten surface")
			moisten_surface(ctx,
							ior=ior.get_value(),
							diffuse_multiplier=diffuse_multiplier.get_value(),
							specular_multiplier=specular_multiplier.get_value(),
							roughness_multiplier=roughness_multiplier.get_value(),
							displacement_blend=displacement_blend_checkbox.get_value(),
							scope_blend=scope_blend_checkbox.get_value(),
							height_blend=height_blend_checkbox.get_value(),
							fractal_blend=fractal_blend_checkbox.get_value(),
							ao_blend=ao_blend_checkbox.get_value(), ix=ix)
			ix.end_command_batch()
			sender.get_window().hide()

	# Window creation
	clarisse_win = ix.application.get_event_window()
	window = ix.api.GuiWindow(clarisse_win, 900, 450, 400, 410)  # Parent, X position, Y position, Width, Height
	window.set_title('Moisten surface')  # Window name

	# Main widget creation
	panel = ix.api.GuiPanel(window, 0, 0, window.get_width(), window.get_height())
	panel.set_constraints(ix.api.GuiWidget.CONSTRAINT_LEFT, ix.api.GuiWidget.CONSTRAINT_TOP,
						  ix.api.GuiWidget.CONSTRAINT_RIGHT, ix.api.GuiWidget.CONSTRAINT_BOTTOM)

	# Form generation
	displacement_blend_label = ix.api.GuiLabel(panel, 10, 10, 150, 22,
											   "Displacement blend: ")
	displacement_blend_checkbox = ix.api.GuiCheckbox(panel, 205, 10, "")
	fractal_blend_label = ix.api.GuiLabel(panel, 10, 40, 150, 22,
										  "Fractal blend: ")
	fractal_blend_checkbox = ix.api.GuiCheckbox(panel, 205, 40, "")
	triplanar_blend_label = ix.api.GuiLabel(panel, 10, 70, 150, 22,
											"Triplanar blend: ")
	triplanar_blend_checkbox = ix.api.GuiCheckbox(panel, 205, 70, "")
	slope_blend_label = ix.api.GuiLabel(panel, 10, 100, 150, 22,
										"Slope blend: ")
	slope_blend_checkbox = ix.api.GuiCheckbox(panel, 205, 100, "")
	scope_blend_label = ix.api.GuiLabel(panel, 10, 130, 150, 22,
										"Scope blend: ")
	scope_blend_checkbox = ix.api.GuiCheckbox(panel, 205, 130, "")
	ao_blend_label = ix.api.GuiLabel(panel, 10, 160, 150, 22,
									 "Occlusion blend: ")
	ao_slope_label2 = ix.api.GuiLabel(panel, 240, 160, 150, 22, "*Slow with displacement")
	ao_blend_checkbox = ix.api.GuiCheckbox(panel, 205, 160, "")
	height_blend_label = ix.api.GuiLabel(panel, 10, 190, 190, 22,
										 "Height blend: ")
	height_blend_checkbox = ix.api.GuiCheckbox(panel, 205, 190, "")

	diffuse_multiplier = ix.api.GuiNumberField(panel, 129, 220, 151, "Diffuse multiply:         ")
	diffuse_multiplier.set_slider_range(0.0, 1)
	specular_multiplier = ix.api.GuiNumberField(panel, 129, 250, 151, "Specular screen:          ")
	specular_multiplier.set_slider_range(0.0, 1)
	roughness_multiplier = ix.api.GuiNumberField(panel, 129, 280, 151, "Roughness multiply:  ")
	roughness_multiplier.set_slider_range(0.0, 1)
	ior = ix.api.GuiNumberField(panel, 129, 310, 151, "IOR:                               ")
	ior.set_slider_range(1.0, 10)

	cancel_btn = ix.api.GuiPushButton(panel, 10, 370, 100, 22, "Close")  # The cancel button (destroy the script window)
	run_btn = ix.api.GuiPushButton(panel, 130, 370, 250, 22, "Apply")  # The run button to run your script

	# init values
	diffuse_multiplier.set_value(MOISTURE_DEFAULT_DIFFUSE_MULTIPLIER)
	specular_multiplier.set_value(MOISTURE_DEFAULT_SPECULAR_MULTIPLIER)
	roughness_multiplier.set_value(MOISTURE_DEFAULT_ROUGHNESS_MULTIPLIER)
	ior.set_value(MOISTURE_DEFAULT_IOR)
	height_blend_checkbox.set_value(True)
	fractal_blend_checkbox.set_value(True)

	# Connect to function
	event_rewire = EventRewire()  # init the class
	event_rewire.connect(cancel_btn, 'EVT_ID_PUSH_BUTTON_CLICK',
						 event_rewire.cancel)
	event_rewire.connect(run_btn, 'EVT_ID_PUSH_BUTTON_CLICK',
						 event_rewire.run)

	# Send all info to clarisse to generate window
	window.show()
	while window.is_shown():    ix.application.check_for_events()
	window.destroy()


moisten_surface_gui()
