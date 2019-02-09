import os
import re
import logging
import random
import subprocess
import platform
import glob
import bisect

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
                        if resolution and resolution not in filename:
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
        search_key = lod if lod else -1
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
        if current_depth <= max_depth or max_depth == 0:
            for result in get_sub_contexts(sub_context, name, max_depth, current_depth, ix=ix):
                if result not in results:
                    results.append(result)
    if name:
        for sub_ctx in results:
            if os.path.basename(str(sub_ctx)) == name:
                return sub_ctx
        return []
    return results


def get_items(ctx, kind=(), max_depth=0, current_depth=0, return_first_hit=False, **kwargs):
    """Gets all items recursively."""
    ix = get_ix(kwargs.get("ix"))
    result = []
    items = ix.api.OfItemVector()
    sub_ctxs = get_sub_contexts(ctx, max_depth=max_depth, current_depth=current_depth, ix=ix)
    sub_ctxs.insert(0, ctx)
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
    triplanar = ix.cmds.CreateObject(tx.get_contextual_name() + TRIPLANAR_SUFFIX, "TextureTriplanar", "Global",
                                     str(ctx))
    connected_attrs = ix.api.OfAttrVector()

    get_attrs_connected_to_texture(tx, connected_attrs, ix=ix)

    for i_attr in range(0, connected_attrs.get_count()):
        ix.cmds.SetTexture([str(connected_attrs[i_attr])], str(triplanar))
    ix.cmds.SetTexture([str(triplanar) + ".right"], str(tx))
    ix.cmds.SetTexture([str(triplanar) + ".left"], str(tx))
    ix.cmds.SetTexture([str(triplanar) + ".top"], str(tx))
    ix.cmds.SetTexture([str(triplanar) + ".bottom"], str(tx))
    ix.cmds.SetTexture([str(triplanar) + ".front"], str(tx))
    ix.cmds.SetTexture([str(triplanar) + ".back"], str(tx))
    ix.cmds.SetValues([str(triplanar) + '.blend', str(triplanar) + '.object_space'],
                      [str(blend), str(object_space)])
    return triplanar


def blur_tx(tx, radius=0.01, quality=DEFAULT_BLUR_QUALITY, **kwargs):
    """Blurs the texture."""
    logging.debug("Blurring selected texture: " + str(tx))
    ix = get_ix(kwargs.get("ix"))
    ctx = tx.get_context()
    blur = ix.cmds.CreateObject(tx.get_contextual_name() + BLUR_SUFFIX, "TextureBlur", "Global", str(ctx))

    connected_attrs = ix.api.OfAttrVector()

    get_attrs_connected_to_texture(tx, connected_attrs, ix=ix)

    for i_attr in range(0, connected_attrs.get_count()):
        ix.cmds.SetTexture([connected_attrs[i_attr].get_full_name()], blur.get_full_name())
    ix.cmds.SetTexture([str(blur) + ".color"], str(tx))
    blur.attrs.radius = radius
    blur.attrs.quality = quality
    return blur


def toggle_map_file_stream(tx, **kwargs):
    """Switches from TextureMapFile to TextureStreamedMapFile."""
    ix = get_ix(kwargs.get("ix"))
    ctx = tx.get_context()
    tx_name = tx.get_contextual_name()
    if tx_name.endswith(PREVIEW_SUFFIX):
        logging.debug("Preview file ignored")
        return None
    temp_name = 'temp_' + ''.join(random.choice('abcdefghijklmnopqrstuvwxyz') for i in range(8))
    delete_items = [str(tx)]
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
            ix.cmds.SetValue(str(reorder_tx) + ".channel_order[0]", ["rrrr"])
            ix.cmds.SetTexture([str(reorder_tx) + ".input"], str(new_tx))
            out_tx = reorder_tx
    elif tx.is_kindof('TextureStreamedMapFile'):
        new_tx = ix.cmds.CreateObject(temp_name, "TextureMapFile", "Global", str(ctx))
        ix.application.check_for_events()
        out_tx = new_tx

        if ix.item_exists(str(ctx) + '/' + tx_name + SINGLE_CHANNEL_SUFFIX):
            reorder_tx = ix.get_item(str(ctx) + '/' + tx_name + SINGLE_CHANNEL_SUFFIX)
            delete_items.append(str(reorder_tx))
            new_tx.attrs.single_channel_file_behavior[0] = 1
    else:
        logging.error('ERROR: No (streamed) map file was selected.')
        return None

    connected_attrs = ix.api.OfAttrVector()
    get_attrs_connected_to_texture(tx, connected_attrs, ix=ix)

    for i_attr in range(0, connected_attrs.get_count()):
        ix.cmds.SetTexture([str(connected_attrs[i_attr])], str(out_tx))

    # Transfer all attributes
    for i in range(0, tx.get_attribute_count()):
        attr_name = str(tx.get_attribute(i)).split('.')[-1]
        if attr_name in ['master_input', 'output_layer', 'u_repeat_mode', 'v_repeat_mode']:
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
                value = [attr.get_string()]
                if value and attr_name == 'filename':
                    udim_file = re.sub(r"((?<!\d)\d{4}(?!\d))", "<UDIM>", os.path.split(value[0])[-1], count=1)
                    value = [os.path.join(os.path.split(value[0])[0], udim_file)]
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


def convert_tx(tx, extension, target_folder=None, replace=True, **kwargs):
    """Converts the selected texture."""
    logging.debug("Converting texture: {} to .{}".format(str(tx), extension))
    ix = get_ix(kwargs.get("ix"))

    file_path = tx.attrs.filename.attr.get_string()
    file_dir = os.path.split(os.path.join(file_path))[0]
    if not target_folder:
        target_folder = file_dir
    filename, ext = os.path.splitext(os.path.basename(file_path))
    if ext.lstrip(".") == "tx":
        ix.log_warning("Cannot convert .tx file back to other formats.")
        return None
    new_file_path = os.path.normpath(
        os.path.join(target_folder, filename + '.' + extension))

    if extension == 'tx':
        executable_name = 'maketx'
        if platform.system() == "Windows":
            executable_name += '.exe'
        if not tx.is_kindof('TextureStreamedMapFile') and replace:
            tx = toggle_map_file_stream(tx, ix=ix)
        converter_path = os.path.normpath(
            os.path.join(ix.application.get_factory().get_vars().get("CLARISSE_BIN_DIR").get_string(), executable_name))
        thread_count = ix.application.get_max_thread_count()
        if thread_count > 32:
            thread_count = 32
        command_string = r'"{}" -v -u --oiio --resize --threads {} "{}" -o "{}"'.format(converter_path, thread_count, file_path, new_file_path)
        logging.debug('Command string:')
        logging.debug(command_string)
    else:
        executable_name = 'iconvert'
        if platform.system() == "Windows":
            executable_name += '.exe'
        converter_path = os.path.normpath(
            os.path.join(ix.application.get_factory().get_vars().get("CLARISSE_BIN_DIR").get_string(), executable_name))
        command_string = r'"{}" "{}" "{}"'.format(converter_path, file_path, new_file_path)
        logging.debug('Command string:')
        logging.debug(command_string)

    if "<UDIM>" in file_path:
        udim_filename_split = file_path.split("<UDIM>")
        udim_files = glob.glob(os.path.join(file_dir, udim_filename_split[0] + '*' + udim_filename_split[1]))
        logging.debug(str(udim_filename_split))
        logging.debug(str(udim_files))
        for udim_file in udim_files:
            udim_command_string = command_string.replace(file_path, udim_file)
            udim_match = re.search(r"((?<!\d)\d{4}(?!\d))", os.path.split(udim_file)[-1])
            logging.debug(udim_match.group(0))
            new_udim_file_path = new_file_path.replace('<UDIM>', str(udim_match.group(0)))
            udim_command_string = udim_command_string.replace(new_file_path, new_udim_file_path)
            logging.debug(udim_command_string)
            conversion = subprocess.Popen(command_string, stdout=subprocess.PIPE, shell=True)
            out, err = conversion.communicate()
            logging.debug(str(out))
            logging.debug(str(err))
            print out
            print err
    else:
        logging.debug(command_string)
        conversion = subprocess.Popen(command_string, stdout=subprocess.PIPE, shell=True)
        out, err = conversion.communicate()
        logging.debug(str(out))
        logging.debug(str(err))
        print out
        print err

    if replace:
        tx.attrs.filename = os.path.normpath(new_file_path)
    return tx
