from clarisse_survival_kit.app import *
from clarisse_survival_kit.utility import check_selection


def toggle_surface_complexity_gui():
    ix.begin_command_batch("Toggle Surface Complexity")
    selection_copy = []
    for selection in ix.selection:
        selection_copy.append(selection)
    if check_selection(selection_copy, is_kindof=["MaterialPhysicalStandard", "MaterialPhysicalBlend",
                                                  "OfContext"]):
        for selected in selection_copy:
            if selected.is_context():
                ctx = selected
            else:
                ctx = selected.get_context()
            toggle_surface_complexity(ctx, ix=ix)
        ix.end_command_batch()
        for selection in selection_copy:
            ix.selection.add(selection)
    else:
        ix.log_warning("Please select either a Physical Standard material or its parent context.")


toggle_surface_complexity_gui()
