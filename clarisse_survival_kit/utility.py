import os
import re
import logging
import random
import subprocess
import platform
import glob
import bisect
import datetime

from clarisse_survival_kit.settings import *


def add_gradient_key(attr, position, color, **kwargs):
    """
    Create a key in the specified gradient attribute with the given position and color.
    If the given color is an array of 3 elements, a 4th is added to have the alpha chanel set to 1.0

    :param attr: The attribute of the gradient for example: <!-- m --><a class="postlink" href="project://gradient.output">project://gradient.output</a><!-- m -->
    :type attr: string or PyOfObject

    :param position: The position of the key you want to set
    :type position: float

    :param color: The color you want to set on the point for example [1, 0, 0] for red
    :type color: list of int

    :return: True or false depending on the sucess of the function.
    """
    ix = get_ix(kwargs.get("ix"))
    if isinstance(attr, str):
        attr = ix.item_exists(attr)
    if not attr:
        ix.log_warning("The specified attribute doesn't exists.")
        return False

    data = []
    if len(color) == 3:
        color.append(1)

    for i in range(len(color)):
        data.append(1.0)
        data.append(0.0)
        data.append(position)
        data.append(float(color[i]))

    ix.cmds.AddCurveValue([str(attr)], data)

    return True


def get_ix(ix_local):
    """Simple function to check if ix is imported or not."""
    try:
        ix
    except NameError:
        return ix_local
    else:
        return ix


def get_textures_from_directory(directory, filename_match_template=FILENAME_MATCH_TEMPLATE,
                                lod_match_template=LOD_MATCH_TEMPLATE, image_formats=IMAGE_FORMATS,
                                resolution=None, lod=None, lod_keys=('normal',)):
    """Returns texture files which exist in the specified directory."""
    logging.debug("Searching for textures inside: " + str(directory))
    logging.debug('Resolution: ' + str(resolution))
    logging.debug('LOD: ' + str(lod))
    textures = {}
    lod_files = {}
    for lod_key in lod_keys:
        lod_files[lod_key] = {}
    for root, dirs, files in os.walk(directory):
        for f in files:
            filename, extension = os.path.splitext(f)
            extension = extension.lower().lstrip('.')
            lod_check = True
            if extension in image_formats:
                logging.debug("Found image: " + str(f))
                path = os.path.normpath(os.path.join(root, f))
                for key, pattern in filename_match_template.iteritems():
                    match = re.search(pattern, filename, re.IGNORECASE)
                    if match:
                        logging.debug("Image matches with: " + str(key))
                        if resolution and resolution not in filename and not 'preview' in filename.lower():
                            logging.debug("Found texture but without specified resolution: " + str(filename))
                            continue
                        lod_match = re.search(lod_match_template, filename, re.IGNORECASE)
                        if lod_match:
                            if lod_match.group('lod'):
                                lod_level = int(lod_match.group('lod'))
                            else:
                                lod_level = -1
                            logging.debug('Texture has LOD level: ' + str(lod_level))
                        if key in lod_keys:
                            logging.debug("LOD texture found: " + str(filename))
                            if lod is not None:
                                logging.debug("Checking if LOD {} matches with filename".format(str(lod)))
                                if lod == -1:
                                    if lod_match:
                                        lod_check = False
                                else:
                                    if lod_match and lod_level != lod:
                                        logging.debug("Texture did not match with LOD level {}".format(str(lod)))
                                        lod_check = False
                                logging.debug("Texture is a LOD normal: " + str(filename))
                        # Check if another file extension exists.
                        # If so use the first that occurs in the image_formats list.
                        if key in textures:
                            previous_extension = os.path.splitext(textures[key])[-1].lstrip('.')
                            if image_formats.index(previous_extension) > image_formats.index(extension):
                                if lod_check:
                                    textures[key] = path
                                else:
                                    lod_files[key][lod_level] = path
                        else:
                            if lod_check:
                                textures[key] = path
                            else:
                                lod_files[key][lod_level] = path
    logging.debug(str(lod_files))
    for lod_key in lod_keys:
        if textures.get(lod_key):
            break
        if not lod_files.get(lod_key):
            logging.debug('No LODs Found.')
            break
        logging.debug('LOD for key "{}" is missing. Trying to pick texture from next LOD level.'.format(lod_key))
        keys = lod_files[lod_key].keys()
        keys.sort()
        search_key = lod if lod is not None else -1
        search_key_index = bisect.bisect(keys, search_key)
        logging.debug(str(search_key_index))
        filename = lod_files[lod_key].get(keys[search_key_index - 1])
        logging.debug('Chose following file as nearest LOD: ' + filename)
        textures[lod_key] = filename

    if textures:
        logging.debug("Textures found in directory: " + directory)
        logging.debug(str(textures))
    else:
        logging.debug("No textures found in directory.")
    return textures


def get_geometry_from_directory(directory):
    """Returns texture files which exist in the specified directory."""
    logging.debug("Searching for meshes inside: " + str(directory))
    meshes = []
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if filename.lower().endswith(('.obj', '.abc', '.lwo')):
                logging.debug("Found mesh file: " + str(filename))
                path = os.path.join(root, filename)
                path = os.path.normpath(path)
                meshes.append(path)
    if meshes:
        logging.debug("Meshes found in directory: " + directory)
        logging.debug(str(meshes))
    else:
        logging.debug("No meshes found in directory.")
    return meshes


def get_stream_map_files(textures):
    """"Returns the files that should be loaded as TextureStreamedMapFile."""
    logging.debug("Searching for streamed map files...")
    stream_map_files = []
    if not textures:
        return []
    for index, texture in textures.iteritems():
        logging.debug("Testing: " + str(textures))
        if type(texture) == list:
            items = get_stream_map_files({str(i): texture[i] for i in range(0, len(texture))})
            for item in items:
                stream_map_files.append(item)
        else:
            filename, extension = os.path.splitext(texture)
            extension = extension.lower().lstrip('.')

            udim_match = re.search(r"((?<!\d)\d{4}(?!\d))", os.path.split(filename)[-1])
            if udim_match or extension == "tx":
                logging.debug("Streamed map file found.")
                stream_map_files.append(index)
    if stream_map_files:
        logging.debug("...found these streamed map files: ")
        logging.debug(str(stream_map_files))
    else:
        logging.debug("...no streamed map files found.")
    return stream_map_files


def get_mtl_from_context(ctx, **kwargs):
    """"Returns the material from the context."""
    ix = get_ix(kwargs.get("ix"))
    ctx_members = get_items(ctx, kind=["MaterialPhysicalStandard", "MaterialPhysicalBlend"], **kwargs)
    mtl = None
    for ctx_member in ctx_members:
        if ctx_member.is_local() and ctx_member.get_contextual_name().endswith(MATERIAL_SUFFIX) or not mtl:
            mtl = ctx_member
    if not mtl:
        logging.debug("No material found in ctx: " + str(ctx))
        return None
    logging.debug("Found material: " + str(mtl))
    return mtl


def get_all_mtls_from_context(ctx, **kwargs):
    """"Returns the material from the context."""
    ix = get_ix(kwargs.get("ix"))
    ctx_members = get_items(ctx, kind=["MaterialPhysicalStandard", "MaterialPhysicalBlend"], **kwargs)
    mtls = []
    for ctx_member in ctx_members:
        if ctx_member.get_contextual_name().endswith(MATERIAL_SUFFIX):
            mtls.append(ctx_member)
    if not mtls:
        logging.debug("No materials found in ctx: " + str(ctx))
        return []
    logging.debug("Found %s materials: " % str(len(mtls)))
    return mtls


def get_disp_from_context(ctx, **kwargs):
    """"Returns the material from the context."""
    ix = get_ix(kwargs.get("ix"))
    objects_array = ix.api.OfObjectArray(ctx.get_object_count())
    flags = ix.api.CoreBitFieldHelper()
    ctx.get_all_objects(objects_array, flags, False)
    disp = None
    for ctx_member in objects_array:
        if check_selection([ctx_member], is_kindof=["Displacement"], max_num=1):
            if ctx_member.is_local() and ctx_member.get_contextual_name().endswith(DISPLACEMENT_MAP_SUFFIX) or not disp:
                disp = ctx_member
    if not disp:
        logging.debug("No displacement found in ctx: " + str(ctx))
        return None
    logging.debug("Found displacement: " + str(disp))
    return disp


def get_textures_connected_to_texture(item, **kwargs):
    """Returns the connected textures to the specified texture as a list."""
    ix = get_ix(kwargs.get("ix"))
    logging.debug('Get textures connected to texture called')
    logging.debug(str(item))
    textures = []
    if not item:
        return textures

    items = ix.api.OfItemArray(1)
    items[0] = item
    output_items = ix.api.OfItemVector()

    ix.application.get_factory().get_items_outputs(items, output_items, False)

    # checks retrieved dependencies
    for i_output in range(0, output_items.get_count()):
        out_item = output_items[i_output]
        logging.debug(str(out_item))
        if out_item.is_object():
            out_obj = out_item.to_object()
            logging.debug(str(out_obj))
            textures.append(out_obj)
    return textures


def check_selection(selection, is_kindof=("",), max_num=0, min_num=1):
    """Simple function to check the kind of objects selected and to limit selection."""
    num = 0
    for item in selection:
        pass_test = False
        for kind in is_kindof:
            if item.is_context():
                if kind == "OfContext":
                    pass_test = True
                    break
            elif item.is_kindof(kind):
                pass_test = True
                break
            elif kind in item.get_class_name():
                pass_test = True
                break
        if not pass_test:
            return False
        else:
            num += 1
    if num < min_num:
        return False
    elif max_num and num > max_num:
        return False
    return True


def check_context(ctx, **kwargs):
    """Tests if you can write to specified context."""
    ix = get_ix(kwargs.get("ix"))
    if (not ctx.is_editable()) or ctx.is_content_locked() or ctx.is_remote():
        ix.log_warning("Cannot write to context, because it's locked.")
        return False
    return True


def get_color_spaces(preset, **kwargs):
    """Gets the installed color spaces for a preset."""
    ix = get_ix(kwargs.get("ix"))
    color_spaces = {}
    installed_color_spaces = ix.api.ColorIO.get_color_space_names()
    for key, choices in preset.items():
        for choice in choices:
            if choice in installed_color_spaces:
                color_spaces[key] = choice
    return color_spaces


def get_sub_contexts(ctx, name="", max_depth=0, current_depth=0, **kwargs):
    """Gets all subcontexts."""
    ix = get_ix(kwargs.get("ix"))
    current_depth += 1
    results = []
    for i in range(ctx.get_context_count()):
        sub_context = ctx.get_context(i)
        results.append(sub_context)
        # 0 is infinite
        if current_depth < max_depth or max_depth == 0:
            for result in get_sub_contexts(sub_context, name, max_depth, current_depth, ix=ix):
                if result not in results:
                    results.append(result)
    if name:
        for sub_ctx in results:
            if os.path.basename(str(sub_ctx)) == name:
                return sub_ctx
        return []
    return results


def get_items(ctx, kind=(), max_depth=0, return_first_hit=False, **kwargs):
    """Gets all items recursively."""
    ix = get_ix(kwargs.get("ix"))
    result = []
    current_depth = 1
    items = ix.api.OfItemVector()
    sub_ctxs = [ctx]
    if max_depth > 1 or max_depth == 0:
        sub_ctxs.extend(get_sub_contexts(ctx, max_depth=max_depth, current_depth=current_depth, ix=ix))
    for sub_ctx in sub_ctxs:
        if sub_ctx.get_object_count():
            objects_array = ix.api.OfObjectArray(sub_ctx.get_object_count())
            flags = ix.api.CoreBitFieldHelper()
            sub_ctx.get_all_objects(objects_array, flags, False)
            for i_obj in range(sub_ctx.get_object_count()):
                if kind:
                    for k in kind:
                        if objects_array[i_obj].is_kindof(k):
                            if return_first_hit:
                                return objects_array[i_obj]
                            items.add(objects_array[i_obj])
                else:
                    items.add(objects_array[i_obj])
    for item in items:
        result.append(item)
    return result


def tx_to_triplanar(tx, blend=0.5, object_space=0, **kwargs):
    """Converts the texture to triplanar."""
    logging.debug("Converting texture to triplanar: " + str(tx))
    ix = get_ix(kwargs.get("ix"))
    ctx = tx.get_context()
    triplanar_tx = ix.cmds.CreateObject(tx.get_contextual_name() + TRIPLANAR_SUFFIX,
                                        "TextureTriplanar", "Global", str(ctx))

    replace_connections(triplanar_tx, tx, ignored_attributes=['runtime_materials', ], ix=ix)

    ix.cmds.SetTexture([str(triplanar_tx) + ".right"], str(tx))
    ix.cmds.SetTexture([str(triplanar_tx) + ".left"], str(tx))
    ix.cmds.SetTexture([str(triplanar_tx) + ".top"], str(tx))
    ix.cmds.SetTexture([str(triplanar_tx) + ".bottom"], str(tx))
    ix.cmds.SetTexture([str(triplanar_tx) + ".front"], str(tx))
    ix.cmds.SetTexture([str(triplanar_tx) + ".back"], str(tx))
    ix.cmds.SetValues([str(triplanar_tx) + '.blend', str(triplanar_tx) + '.object_space'],
                      [str(blend), str(object_space)])
    return triplanar_tx


def blur_tx(tx, radius=0.01, quality=DEFAULT_BLUR_QUALITY, **kwargs):
    """Blurs the texture."""
    logging.debug("Blurring selected texture: " + str(tx))
    ix = get_ix(kwargs.get("ix"))
    ctx = tx.get_context()
    blur = ix.cmds.CreateObject(tx.get_contextual_name() + BLUR_SUFFIX, "TextureBlur", "Global", str(ctx))

    replace_connections(blur, tx, ignored_attributes=['runtime_materials', ], ix=ix)
    ix.cmds.SetTexture([str(blur) + ".color"], str(tx))
    blur.attrs.radius = radius
    blur.attrs.quality = quality
    return blur


def quick_blend(items, **kwargs):
    """Quickly blends two or more items."""
    ix = get_ix(kwargs.get("ix"))
    item_a = items[0]
    item_b = items[1]
    logging.debug("Blending selected items: {} {}".format(str(item_a), str(item_b)))
    ctx = item_a.get_context()
    if len(items) > 8:
        ix.log_warning("Too many items selected. Up to 8 items can be blended.")
        return None

    if check_selection(items, ['TextureNormalMap'], min_num=2):
        blend_tx = ix.cmds.CreateObject(item_a.get_contextual_name() + MULTI_BLEND_SUFFIX, "TextureMultiBlend",
                                        "Global", str(ctx))
        ix.cmds.SetValue(str(blend_tx) + ".enable_layer_1", [str(1)])
        ix.application.check_for_events()
        normal_tx_value = ix.get_item(str(item_a) + ".input")
        if normal_tx_value:
            normal_tx = normal_tx_value.get_texture()
            if normal_tx:
                ix.cmds.SetTexture([str(blend_tx) + ".layer_1_color"], str(normal_tx))
        for item in items[1:]:
            item_index = items.index(item) + 1
            ix.cmds.SetValue(str(blend_tx) + ".enable_layer_{}".format(str(item_index)), [str(1)])
            ix.cmds.SetValue(str(blend_tx) + ".layer_{}_mode".format(str(item_index)), [str(10)])
            ix.application.check_for_events()
            item_normal_tx_value = ix.get_item(str(item) + ".input")
            if item_normal_tx_value:
                item_normal_tx = item_normal_tx_value.get_texture()
                if item_normal_tx:
                    ix.cmds.SetTexture([str(blend_tx) + ".layer_{}_color".format(str(item_index))],
                                       str(item_normal_tx))

        ix.cmds.SetTexture([str(item_a) + ".input"], str(blend_tx))
        return blend_tx
    elif check_selection(items, ['Texture'], min_num=2):
        print "Mixing Textures"
        if len(items) == 2:
            blend_tx = ix.cmds.CreateObject(item_a.get_contextual_name() + BLEND_SUFFIX, "TextureBlend",
                                            "Global", str(ctx))
        else:
            blend_tx = ix.cmds.CreateObject(item_a.get_contextual_name() + MULTI_BLEND_SUFFIX, "TextureMultiBlend",
                                            "Global", str(ctx))

        replace_connections(blend_tx, item_a, ignored_attributes=['runtime_materials', ], ix=ix)

        if len(items) == 2:
            ix.cmds.SetTexture([str(blend_tx) + ".input1"], str(item_a))
            ix.cmds.SetTexture([str(blend_tx) + ".input2"], str(item_b))
        else:
            ix.cmds.SetValue(str(blend_tx) + ".enable_layer_1", [str(1)])
            ix.application.check_for_events()
            ix.cmds.SetTexture([str(blend_tx) + ".layer_1_color"], str(item_a))
            for item in items[1:]:
                item_index = items.index(item) + 1
                ix.cmds.SetValue(str(blend_tx) + ".enable_layer_{}".format(str(item_index)), [str(1)])
                ix.application.check_for_events()
                ix.cmds.SetTexture([str(blend_tx) + ".layer_{}_color".format(str(item_index))], str(item))
        return blend_tx
    elif check_selection(items, ['MaterialPhysical'], min_num=2):
        print "Mixing Materials"
        if len(items) == 2:
            blend_mtl = ix.cmds.CreateObject(item_a.get_contextual_name() + MIX_SUFFIX, "MaterialPhysicalBlend",
                                             "Global", str(ctx))
        else:
            if len(items) > 6:
                ix.log_warning("Too many items selected. Up to 6 materials can be mixed.")
                return None
            blend_mtl = ix.cmds.CreateObject(item_a.get_contextual_name() + MIX_SUFFIX,
                                             "MaterialPhysicalMultiblend", "Global", str(ctx))

        replace_connections(blend_mtl, item_a, ignored_attributes=['runtime_materials', ], ix=ix)

        if len(items) == 2:
            ix.cmds.SetValue(str(blend_mtl) + ".input1", [str(item_a)])
            ix.cmds.SetValue(str(blend_mtl) + ".input2", [str(item_b)])
        else:
            for item in items:
                item_index = items.index(item) + 1
                ix.cmds.SetValue(str(blend_mtl) + ".enable_layer_{}".format(str(item_index)), [str(1)])
                ix.application.check_for_events()
                ix.cmds.SetValues([str(blend_mtl) + ".layer_{}".format(str(item_index))], [str(item)])

        return blend_mtl
    elif check_selection(items, ['Displacement'], min_num=2):
        if len(items) == 2:
            blend_tx = ix.cmds.CreateObject(item_a.get_contextual_name() + BLEND_SUFFIX, "TextureBlend", "Global",
                                            str(ctx))
        else:
            blend_tx = ix.cmds.CreateObject(item_a.get_contextual_name() + MULTI_BLEND_SUFFIX, "TextureMultiBlend",
                                            "Global", str(ctx))
        item_disp_offset_txs = []
        for item in items:
            item_srf_height = item.attrs.front_value[0]
            item_disp_tx_front_value = ix.get_item(str(item) + ".front_value")
            item_disp_tx = item_disp_tx_front_value.get_texture()
            item_disp_height_scale_tx = ix.cmds.CreateObject(
                item.get_contextual_name() + DISPLACEMENT_HEIGHT_SCALE_SUFFIX,
                "TextureMultiply", "Global", str(ctx))
            ix.cmds.SetTexture([str(item_disp_height_scale_tx) + ".input1"], str(item_disp_tx))
            item_disp_height_scale_tx.attrs.input2[0] = item_srf_height
            item_disp_height_scale_tx.attrs.input2[1] = item_srf_height
            item_disp_height_scale_tx.attrs.input2[2] = item_srf_height

            item_disp_offset_tx = ix.cmds.CreateObject(item.get_contextual_name() + DISPLACEMENT_OFFSET_SUFFIX,
                                                       "TextureSubtract",
                                                       "Global", str(ctx))
            item_disp_offset_tx.attrs.input2[0] = item_srf_height + 0.5
            item_disp_offset_tx.attrs.input2[1] = item_srf_height + 0.5
            item_disp_offset_tx.attrs.input2[2] = item_srf_height + 0.5
            ix.cmds.SetTexture([str(item_disp_offset_tx) + ".input1"], str(item_disp_height_scale_tx))
            item_disp_offset_txs.append(item_disp_offset_tx)

        item_a.attrs.bound[0] = 1
        item_a.attrs.bound[1] = 1
        item_a.attrs.bound[2] = 1
        item_a.attrs.front_value = 1
        item_a.attrs.front_offset = -0.5

        if len(items) == 2:
            ix.cmds.SetTexture([str(blend_tx) + ".input1"], str(item_disp_offset_txs[0]))
            ix.cmds.SetTexture([str(blend_tx) + ".input2"], str(item_disp_offset_txs[1]))
        else:
            ix.cmds.SetValue(str(blend_tx) + ".enable_layer_1", [str(1)])
            ix.application.check_for_events()
            ix.cmds.SetTexture([str(blend_tx) + ".layer_1_color"], str(item_disp_offset_txs[0]))
            for item in items[1:]:
                item_index = items.index(item) + 1
                ix.cmds.SetValue(str(blend_tx) + ".enable_layer_{}".format(str(item_index)), [str(1)])
                ix.application.check_for_events()
                ix.cmds.SetTexture([str(blend_tx) + ".layer_{}_color".format(str(item_index))],
                                   str(item_disp_offset_txs[items.index(item)]))

        ix.cmds.SetTexture([str(item_a) + ".front_value"], str(blend_tx))

        return blend_tx

    else:
        ix.log_warning("ERROR: Couldn't mix the selected items. \n"
                       "Make sure to select either two or more Texture items, Normal Maps, Displacement Maps or PhysicalMaterials. \n"
                       "Texture items can be of any type. Materials can only be of Physical category.")
        return False


def get_attrs_connected_to_item(item, **kwargs):
    """
    This searches for occourences of the selected texture item in other textures or objects/shading rules.
    """
    ix = get_ix(kwargs.get("ix"))

    connected_attrs = []
    if not item:
        return connected_attrs

    items = ix.api.OfItemArray(1)
    items[0] = item
    output_items = ix.api.OfItemVector()

    ix.application.get_factory().get_items_outputs(items, output_items, False)

    logging.debug('Retrieving connected attributes')
    # checks retrieved dependencies
    for i_output in range(0, output_items.get_count()):
        out_item = output_items[i_output]
        if out_item.is_object():
            out_obj = out_item.to_object()
            # Shading layers need to be handled differently
            if out_obj.is_kindof('ShadingLayer'):
                connected_attrs.append(str(out_obj))
            else:
                attr_count = out_obj.get_attribute_count()
                for i_attr in range(0, attr_count):
                    attr = out_obj.get_attribute(i_attr)
                    attr_str = str(attr)
                    attr_type = attr.get_type()
                    attr_container = attr.get_container()
                    # Object references
                    if attr_type in [5, 6]:
                        if attr_container in [1, 2]:
                            objects = ix.api.OfObjectVector()
                            attr.get_values(objects)
                            for i_obj in range(0, objects.get_count()):
                                if str(objects[i_obj]) == str(item):
                                    connected_attrs.append(attr_str + '[{}]'.format(str(i_obj)))
                        elif str(attr.get_object()) == str(item):
                            connected_attrs.append(attr_str)
                    # String references
                    elif attr_type in [3, 4]:
                        if str(attr.get_string()) == str(item):
                            connected_attrs.append(attr_str)
                    # Texture inputs
                    elif attr.is_textured() and str(attr.get_texture()) == str(item):
                        connected_attrs.append(attr_str)
    return connected_attrs


def replace_connections(new_item, old_item, source_item=None, ignored_attributes=(), ignored_classes=(), **kwargs):
    """Swap existing material/texture connections with another."""
    ix = get_ix(kwargs.get("ix"))

    if not source_item:
        source_item = old_item

    connected_attrs = get_attrs_connected_to_item(source_item, ix=ix)
    logging.debug('Swapping {} item connections'.format(str(len(connected_attrs))))
    for connected_attr in connected_attrs:
        logging.debug(str(connected_attr))
        attr = ix.get_item(connected_attr)
        # Ignore object if in ignored classes
        if hasattr(connected_attr, 'get_class_name') and connected_attr.get_class_name() in ignored_classes:
            continue
        # You mustn't fetch shading layer inputs directly via attributes. You need to use get_rule_value
        elif hasattr(connected_attr, 'is_kindof') and connected_attr.is_kindof('ShadingLayer'):
            logging.debug('Attribute is Shading Layer')
            columns = ["material", "clip_map", "displacement"]
            sl_module = connected_attr.get_module()
            rules = sl_module.get_rules()
            for row in range(0, rules.get_count()):
                for column in columns:
                    if str(sl_module.get_rule_value(row, column)) == str(old_item):
                        logging.debug('Swapping rule value index: {}, column: {}'.format(row, column))
                        sl_module.set_rule_value(row, column, str(new_item))
                        ix.application.check_for_events()
        # Attributes
        else:
            attr_name = attr.get_name()
            logging.debug('Attribute name: ' + attr_name)
            parent_obj = attr.get_parent_object()
            logging.debug('Parent node: ' + str(parent_obj))
            logging.debug('Parent class: ' + parent_obj.get_class_name())
            if attr_name in ignored_attributes:
                logging.debug('Ignoring attribute')
                continue
            # Object references
            if attr.get_type() in [5, 6]:
                logging.debug('Type: Object reference')
                ix.cmds.SetValues([str(connected_attr)], [str(new_item)])
            # Texture connections
            else:
                logging.debug('Type: Texture')
                ix.cmds.SetTexture([str(connected_attr)], str(new_item))


def toggle_map_file_stream(tx, **kwargs):
    """Switches from TextureMapFile to TextureStreamedMapFile and vice versa."""
    ix = get_ix(kwargs.get("ix"))
    ctx = tx.get_context()
    tx_name = tx.get_contextual_name()
    if tx_name.endswith(PREVIEW_SUFFIX):
        logging.debug("Preview file ignored")
        return None
    temp_name = 'temp_' + ''.join(random.choice('abcdefghijklmnopqrstuvwxyz') for i in range(8))
    delete_items = [str(tx)]
    reorder_tx = None

    if tx.is_kindof('TextureMapFile'):
        new_tx = ix.cmds.CreateObject(temp_name, "TextureStreamedMapFile", "Global", str(ctx))
        default_color_space = ix.api.ColorIO.get_color_space_names()[0]
        ix.cmds.SetValue(str(new_tx) + '.color_space_auto_detect', [str(0)])
        ix.application.check_for_events()
        ix.cmds.SetValue(str(new_tx) + '.color_space', [default_color_space])

        single_channel = tx.attrs.single_channel_file_behavior[0] == 1
        out_tx = new_tx
        if single_channel:
            logging.debug("Creating reorder node...")
            reorder_tx = ix.cmds.CreateObject(tx_name + SINGLE_CHANNEL_SUFFIX, "TextureReorder",
                                              "Global", str(ctx))
            ix.cmds.SetValue(str(reorder_tx) + ".channel_order[0]", ["rrr1"])
            ix.cmds.SetTexture([str(reorder_tx) + ".input"], str(new_tx))
            out_tx = reorder_tx
    elif tx.is_kindof('TextureStreamedMapFile'):
        new_tx = ix.cmds.CreateObject(temp_name, "TextureMapFile", "Global", str(ctx))
        ix.application.check_for_events()
        out_tx = new_tx

        connected_textures = get_textures_connected_to_texture(tx, ix=ix)
        for connected_texture in connected_textures:
            logging.debug(str(connected_texture))
            if connected_texture.is_kindof('TextureReorder'):
                if connected_texture.attrs.channel_order.attr.get_string() in ['rrrr','rrr1']:
                    logging.debug('Found matching reorder node')
                    reorder_tx = connected_texture
                    delete_items.append(str(reorder_tx))
                    new_tx.attrs.single_channel_file_behavior[0] = 1
    else:
        logging.error('ERROR: No (streamed) map file was selected.')
        return None

    source_item = reorder_tx if tx.is_kindof('TextureStreamedMapFile') else None

    replace_connections(out_tx, tx, source_item=source_item, ignored_attributes=['runtime_materials', ], ix=ix)

    # Transfer all attributes
    filename_sys_value = []
    for i in range(0, tx.get_attribute_count()):
        attr_name = str(tx.get_attribute(i)).split('.')[-1]
        if attr_name in ['master_input', 'output_layer', 'u_repeat_mode', 'v_repeat_mode',
                         'detect_sequence', 'sequence_mode', 'default_color', 'interpolation_mode', ]:
            continue
        # Check if the stream map file has the same attributes.
        # .single_channel_file_behavior isn't available in streamed map files.
        if new_tx.attribute_exists(attr_name):
            logging.debug("Copying attribute: " + attr_name)
            attr = tx.get_attribute(attr_name)
            if attr.is_locked() or not attr.is_editable():
                logging.debug("Attribute was locked")
                continue
            attr_type = attr.get_type_name(attr.get_type())
            logging.debug("Attr type: " + attr_type)
            if attr_type == 'TYPE_STRING':
                value = [r'{}'.format(attr.get_string())]
                logging.debug(str(value))
                if value and attr_name in ['filename', 'filename_sys']:
                    directory, filename = os.path.split(r"{}".format(value[0]))
                    directory = directory.replace("\\", "/")
                    logging.debug(directory)
                    name, extension = os.path.splitext(filename)
                    switch_extension = ''
                    if filename:
                        files = glob.glob(r"{}/{}.*".format(directory, name.replace('<UDIM>', '*')))
                        if len(files) > 1:
                            other_extensions = []
                            for f in files:
                                if not f.endswith(extension):
                                    f_name, f_extension = os.path.splitext(f)
                                    if f_extension.lstrip('.') not in other_extensions:
                                        other_extensions.append(f_extension.lstrip('.'))
                            for other_extension in other_extensions:
                                if not switch_extension:
                                    switch_extension = other_extension
                                else:
                                    if IMAGE_FORMATS.index(other_extension) > IMAGE_FORMATS.index(switch_extension):
                                        switch_extension = other_extension
                    if not switch_extension:
                        switch_extension = extension.lstrip('.')
                    udim_file = re.sub(r"((?<!\d)\d{4}(?!\d))", "<UDIM>", name + '.' + switch_extension, count=1)
                    logging.debug(udim_file)
                    if attr_name == 'filename_sys':
                        value = filename_sys_value
                    else:
                        value = [r"{}/{}".format(directory, udim_file)]
                        filename_sys_value = value
            elif attr_type == 'TYPE_BOOL':
                value_bool = attr.get_bool()
                value = [str(1) if value_bool else str(0)]
            elif attr_type in ['TYPE_LONG', 'TYPE_DOUBLE']:
                value_list = eval(str(getattr(tx.attrs, attr_name, '')))
                value = [str(v) for v in value_list]
            else:
                continue
            logging.debug("Value: " + str(value))
            ix.cmds.SetValue(str(new_tx) + '.' + attr_name, value)
    ix.cmds.DeleteItems(delete_items)
    if new_tx.is_kindof('TextureStreamedMapFile'):
        ix.cmds.SetValue(str(new_tx) + '.interpolation_mode', [str(3)])
        ix.cmds.SetValue(str(new_tx) + '.mipmap_mode', [str(3)])
    ix.application.check_for_events()
    ix.cmds.RenameItem(str(new_tx), tx_name)
    return new_tx


def convert_tx(tx, extension, target_folder=None, replace=True, update=False, **kwargs):
    """Converts the selected texture. Update argument will force newer files to be reconverted."""
    logging.debug("Converting texture: {} to .{}".format(str(tx), extension))
    ix = get_ix(kwargs.get("ix"))

    file_path = tx.attrs.filename.attr.get_string()
    file_dir = os.path.split(os.path.join(file_path))[0]
    if not target_folder:
        target_folder = file_dir
    source_filename, source_ext = os.path.splitext(os.path.basename(file_path))

    new_file_path = os.path.normpath(
        os.path.join(target_folder, source_filename + '.' + extension))

    thread_count = ix.application.get_max_thread_count()
    if thread_count > 32:
        thread_count = 32

    command_arguments = {'threads': thread_count}
    clarisse_dir = ix.application.get_factory().get_vars().get("CLARISSE_BIN_DIR").get_string()

    if extension == 'tx':
        executable_name = 'maketx'
        if platform.system().lower() == "windows":
            executable_name += '.exe'
        elif platform.system().lower().startswith("linux"):
            os.environ['LD_LIBRARY_PATH'] = os.path.normpath(clarisse_dir)
        elif platform.system().lower() == "darwin":
            os.environ['DYLD_LIBRARY_PATH'] = os.path.normpath(clarisse_dir)

        if not tx.is_kindof('TextureStreamedMapFile') and replace:
            tx = toggle_map_file_stream(tx, ix=ix)
        converter_path = os.path.normpath(os.path.join(clarisse_dir, executable_name))
        command_arguments['converter'] = converter_path
        command_string = r'"{converter}" -v -u --oiio --resize --threads {threads} "{old_file}" -o "{new_file}"'
        logging.debug('Command string:')
        logging.debug(command_string)
    else:
        executable_name = 'iconvert'
        if tx.is_kindof('TextureStreamedMapFile') and source_ext in ['.tx', '.tex'] and replace:
            tx = toggle_map_file_stream(tx, ix=ix)
        if platform.system() == "Windows":
            executable_name += '.exe'
        elif platform.system().lower().startswith("linux"):
            os.environ['LD_LIBRARY_PATH'] = os.path.normpath(clarisse_dir)
        elif platform.system().lower() == "darwin":
            os.environ['DYLD_LIBRARY_PATH'] = os.path.normpath(clarisse_dir)
        converter_path = os.path.normpath(os.path.join(clarisse_dir, executable_name))
        command_arguments['converter'] = converter_path
        command_string = r'"{converter}" --threads 0 "{old_file}" "{new_file}"'
        logging.debug('Command string:')
        logging.debug(command_string)

    # Search for source and newer files that need to be updated
    conversion_files = []
    source_files = glob.glob(os.path.join(file_dir, source_filename.replace('<UDIM>', '*')) + source_ext)
    logging.debug('Source files:')
    logging.debug('\n'.join(source_files))
    other_files = glob.glob(os.path.join(file_dir, source_filename.replace('<UDIM>', '*')) + '.*')
    logging.debug('Other files:')
    logging.debug('\n'.join(other_files))
    if not source_files == other_files and update:
        for f in other_files:
            matching_source = os.path.splitext(f)[0] + source_ext
            other_mtime = datetime.datetime.fromtimestamp(os.path.getmtime(f))
            source_mtime = datetime.datetime.fromtimestamp(os.path.getmtime(matching_source))
            if other_mtime >= source_mtime:
                logging.debug('Found newer or equal file in directy: ' + f)
                logging.debug('Time of file a: ' + str(other_mtime))
                logging.debug('Time of file b: ' + str(source_mtime))
                print 'Found newer or equal file in directory: ' + f
                conversion_files.append(f)
    else:
        conversion_files = source_files

    logging.debug('Conversion files:')
    logging.debug('\n'.join(conversion_files))

    for conversion_file in conversion_files:
        conversion_file_arguments = command_arguments
        command_arguments['old_file'] = conversion_file
        command_arguments['new_file'] = os.path.splitext(conversion_file)[0] + '.' + extension
        if target_folder != file_dir:
            command_arguments['new_file'] = os.path.join(target_folder, os.path.basename(command_arguments['new_file']))
        else:
            pass
        if command_arguments['old_file'] == command_arguments['new_file']:
            logging.debug('File ignored because input same as output: ' + conversion_file)
            continue
        formatted_command_string = command_string.format(**conversion_file_arguments)
        logging.debug(formatted_command_string)
        conversion = subprocess.Popen(formatted_command_string, stdout=subprocess.PIPE, shell=True)
        out, err = conversion.communicate()
        if out.strip():
            logging.debug(str(out))
            print out
        if err:
            logging.debug(str(err))
            print err
        if err or not os.path.exists(command_arguments['new_file']) or \
                        os.path.getsize(command_arguments['new_file']) < 10:
            error_msg = 'ERROR: File has not been converted. Failed to find new converted file: ' + \
                        command_arguments['new_file']
            print error_msg
            ix.log_error(error_msg)
            return tx
        try:
            os.utime(command_arguments['new_file'], None)
        except Exception:
            logging.debug('******ERROR couldn\'t set utime in file******')
            pass

    if replace:
        tx.attrs.filename = os.path.normpath(new_file_path)
    return tx
