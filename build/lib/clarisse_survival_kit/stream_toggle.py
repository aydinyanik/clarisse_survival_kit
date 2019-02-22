from clarisse_survival_kit.app import *
from clarisse_survival_kit.utility import check_selection


def toggle_tx_stream_gui():
    selection_copy = []
    for selection in ix.selection:
        selection_copy.append(selection)
    new_selection = []
    if check_selection(selection_copy, is_kindof=["TextureMapFile", "TextureStreamedMapFile", "OfContext"]):
        ix.begin_command_batch("Toggle texture stream")
        for selected in selection_copy:
            if selected.is_context():
                texture_maps = get_items(selected, kind=["TextureMapFile", "TextureStreamedMapFile"], ix=ix)
                for texture_map in texture_maps:
                    tx = toggle_map_file_stream(tx=texture_map, ix=ix)
                    if tx:
                        new_selection.append(tx)
            else:
                tx = toggle_map_file_stream(tx=selected, ix=ix)
                if tx:
                    new_selection.append(tx)
        ix.end_command_batch()
        ix.selection.deselect_all()
        ix.application.check_for_events()
        for selection in new_selection:
            ix.selection.add(selection)
    else:
        ix.log_warning("Please one or more texture of type: TextureMapFile or TextureStreamedMapFile "
                       "or a Context that contains these types.")


toggle_tx_stream_gui()
