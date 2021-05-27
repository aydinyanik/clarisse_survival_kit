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


def reconverter_gui():
    textures = get_selected_textures()
    if not textures:
        return
    ix.begin_command_batch("Reconvert")
    progress = ix.application.create_progress_bar('Converting textures...')
    progress.set_value(0.0)
    progress.set_step_count(len(textures))
    progress.start()
    i = 0
    for tx in textures:
        if tx:
            filename = tx.attrs.filename.attr.get_string()
            if filename:
                extension = os.path.splitext(filename)[-1].lstrip('.')
                convert_tx(tx, extension=extension, replace=True, update=True, ix=ix)
        progress.step(i)
        i += 1
        ix.application.check_for_events()
    progress.destroy()
    ix.end_command_batch()


reconverter_gui()
