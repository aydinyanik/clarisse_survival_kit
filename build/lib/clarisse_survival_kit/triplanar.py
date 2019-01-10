from clarisse_survival_kit.app import *
from clarisse_survival_kit.utility import check_selection


def textures_to_triplanar_gui():
	result = {'object_space': 0}

	class EventRewire(ix.api.EventObject):
		def os_base_refresh(self, sender, evtid):
			result['object_space'] = 0
			os_world_checkbox.set_value(False)
			os_base_checkbox.set_value(True)

		def os_world_refresh(self, sender, evtid):
			result['object_space'] = 2
			os_world_checkbox.set_value(True)
			os_base_checkbox.set_value(False)

		def cancel(self, sender, evtid):
			sender.get_window().hide()

		def run(self, sender, evtid):
			textures = []
			for selected in ix.selection:
				if check_selection([selected], is_kindof=["Texture"]):
					textures.append(selected)
				else:
					ix.log_warning("One or more selected items are not texture objects.")
			ix.begin_command_batch("Textures to Triplanar")
			triplanar_textures = []
			for tx in textures:
				triplanar_textures.append(tx_to_triplanar(tx, blend=ratio_field.get_value(),
														  object_space=result.get('object_space'),
														  ix=ix))
			if triplanar_textures:
				ix.selection.deselect_all()
				for tx in triplanar_textures:
					ix.selection.add(tx)
			ix.end_command_batch()
			sender.get_window().hide()

	# Window creation
	clarisse_win = ix.application.get_event_window()
	window = ix.api.GuiWindow(clarisse_win, 900, 450, 400, 120)  # Parent, X position, Y position, Width, Height
	window.set_title('Textures to Triplanar')  # Window name

	# Main widget creation
	panel = ix.api.GuiPanel(window, 0, 0, window.get_width(), window.get_height())
	panel.set_constraints(ix.api.GuiWidget.CONSTRAINT_LEFT, ix.api.GuiWidget.CONSTRAINT_TOP,
						  ix.api.GuiWidget.CONSTRAINT_RIGHT, ix.api.GuiWidget.CONSTRAINT_BOTTOM)

	# Form generation
	ratio_field = ix.api.GuiNumberField(panel, 70, 10, 320, "Blend ratio")
	ratio_field.set_slider_range(0, 1)
	ratio_field.set_increment(0.1)
	ratio_field.enable_slider_range(True)

	os_base_label = ix.api.GuiLabel(panel, 10, 40, 150, 22,
									"Object Space (Base): ")
	os_base_checkbox = ix.api.GuiCheckbox(panel, 180, 40, "")
	os_world_label = ix.api.GuiLabel(panel, 220, 40, 150, 22,
									 "Object Space (World): ")
	os_world_checkbox = ix.api.GuiCheckbox(panel, 370, 40, "")

	cancelBtn = ix.api.GuiPushButton(panel, 10, 90, 100, 22, "Cancel")  # The cancel button (destroy the script window)
	runBtn = ix.api.GuiPushButton(panel, 130, 90, 250, 22, "Convert")  # The run button to run your script

	# init values
	ratio_field.set_value(0.5)
	os_base_checkbox.set_value(True)

	# Connect to function
	event_rewire = EventRewire()  # init the class

	event_rewire.connect(cancelBtn, 'EVT_ID_PUSH_BUTTON_CLICK',
						 event_rewire.cancel)
	event_rewire.connect(runBtn, 'EVT_ID_PUSH_BUTTON_CLICK',
						 event_rewire.run)
	event_rewire.connect(os_base_checkbox, 'EVT_ID_CHECKBOX_CLICK',
						 event_rewire.os_base_refresh)
	event_rewire.connect(os_world_checkbox, 'EVT_ID_CHECKBOX_CLICK',
						 event_rewire.os_world_refresh)

	# Send all info to clarisse to generate window
	window.show()
	while window.is_shown():    ix.application.check_for_events()
	window.destroy()


textures_to_triplanar_gui()
