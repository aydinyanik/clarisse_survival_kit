import os
import re
import logging

from clarisse_survival_kit.settings import IMAGE_FORMATS, FILENAME_MATCH_TEMPLATE, MATERIAL_SUFFIX, \
    DISPLACEMENT_MAP_SUFFIX


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


def get_textures_from_directory(directory):
    """Returns texture files which exist in the specified directory."""
    logging.debug("Searching for textures inside: " + str(directory))
    files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    textures = {}
    for f in files:
        filename, extension = os.path.splitext(f)
        extension = extension.lower().lstrip('.')
        if extension in IMAGE_FORMATS:
            logging.debug("Found image: " + str(f))
            path = os.path.join(directory, f)
            path = os.path.normpath(path)
            for key, pattern in FILENAME_MATCH_TEMPLATE.iteritems():
                match = re.search(pattern, filename, re.IGNORECASE)
                if match:
                    logging.debug("Image matches with: " + str(key))
                    if key == 'normal_lods':
                        if type(textures.get(key)) != list:
                            textures[key] = []
                        else:
                            # Check if another file extension exists.
                            # If so use the first that occurs in the IMAGE_FORMATS list.
                            previous_extension = os.path.splitext(textures[key][-1])[-1].lstrip('.')
                            if IMAGE_FORMATS.index(previous_extension) > IMAGE_FORMATS.index(extension):
                                textures[key] = path
                                continue
                        textures[key].append(path)
                    else:
                        # Check if another file extension exists.
                        # If so use the first that occurs in the IMAGE_FORMATS list.
                        if key in textures:
                            previous_extension = os.path.splitext(textures[key])[-1].lstrip('.')
                            if IMAGE_FORMATS.index(previous_extension) > IMAGE_FORMATS.index(extension):
                                textures[key] = path
                        else:
                            textures[key] = path
    if textures:
        logging.debug("Textures found in directory: " + directory)
        logging.debug(str(textures))
    else:
        logging.debug("No textures found in directory.")
    return textures


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

            udim_match = re.search(r"((?<!\d)\d{4}(?!\d))", filename)
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
    objects_array = ix.api.OfObjectArray(ctx.get_object_count())
    flags = ix.api.CoreBitFieldHelper()
    ctx.get_all_objects(objects_array, flags, False)
    mtl = None
    for ctx_member in objects_array:
        if check_selection([ctx_member], is_kindof=["MaterialPhysicalStandard", "MaterialPhysicalBlend"], max_num=1):
            if ctx_member.is_local() and ctx_member.get_contextual_name().endswith(MATERIAL_SUFFIX) or not mtl:
                mtl = ctx_member
    if not mtl:
        logging.debug("No material found in ctx: " + str(ctx))
        return None
    logging.debug("Found material: " + str(mtl))
    return mtl


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


def get_attrs_connected_to_texture(texture_item, connected_attrs, **kwargs):
    """
    This searches for occourences of the selected texture item in other textures.
    Original function was written by Isotropix. I made a modification so it also searches for strings.
    The MaterialPhysicalBlend doesn't use SetTextures(), but SetValues().
    The only way to retrieve the connected values were by using get_string().
    """
    ix = get_ix(kwargs.get("ix"))
    # Script by Isotropix
    # temporary variables needed to call get_items_outputs on the factory
    items = ix.api.OfItemArray(1)
    items[0] = texture_item
    output_items = ix.api.OfItemVector()

    # let's call the get_items_outputs like in the context selection toolbar;
    # last parameter 'False' means no recursivity on getting dependencies
    ix.application.get_factory().get_items_outputs(items, output_items, False)

    # checks retrieved dependencies
    for i_output in range(0, output_items.get_count()):
        out_item = output_items[i_output]
        if out_item.is_object():
            out_obj = out_item.to_object()
            attr_count = out_obj.get_attribute_count()
            for i_attr in range(0, attr_count):
                attr = out_obj.get_attribute(i_attr)
                if (attr.is_textured() and str(attr.get_texture()) == str(texture_item)) or \
                        (attr.get_string() == str(texture_item)):
                    connected_attrs.add(attr)


def get_textures_connected_to_texture(texture_item, **kwargs):
    """Returns the connected textures to the specified texture as a list."""
    ix = get_ix(kwargs.get("ix"))
    # Script by Isotropix
    # temporary variables needed to call get_items_outputs on the factory
    items = ix.api.OfItemArray(1)
    items[0] = texture_item
    output_items = ix.api.OfItemVector()

    # let's call the get_items_outputs like in the context selection toolbar;
    # last parameter 'False' means no recursivity on getting dependencies
    ix.application.get_factory().get_items_outputs(items, output_items, False)

    # checks retrieved dependencies
    textures = []
    for i_output in range(0, output_items.get_count()):
        out_item = output_items[i_output]
        if out_item.is_object():
            out_obj = out_item.to_object()
            textures.append(out_obj)
    return textures


def check_selection(selection, is_kindof=[""], max_num=0, min_num=1):
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
    if (not ctx.is_editable()) and ctx.is_content_locked() and ctx.is_remote():
        ix.log_error("Cannot write to context, because it's locked.")
        return False
    return True
