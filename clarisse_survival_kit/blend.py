from clarisse_survival_kit.app import *
from clarisse_survival_kit.utility import check_selection, quick_blend


def blend_gui():
    selection_copy = []
    for selection in ix.selection:
        selection_copy.append(selection)
    if check_selection(selection_copy, is_kindof=["Texture", "MaterialPhysical", "Displacement", "TextureNormalMap"],
                       min_num=2):
        ix.begin_command_batch("Blend items")
        blend_tx = quick_blend(selection_copy, ix=ix)
        ix.end_command_batch()
        ix.selection.deselect_all()
        ix.selection.add(blend_tx)
    else:
        print "heeere"
        ix.log_warning("ERROR: Couldn't mix the selected items. \n"
                       "Make sure to select either two texture items or two PhysicalMaterials. \n"
                       "Texture items can be of any type. Materials can only be of Physical category.")


blend_gui()
