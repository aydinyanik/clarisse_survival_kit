from clarisse_survival_kit.selectors import *
from clarisse_survival_kit.utility import *
from clarisse_survival_kit.surface import Surface
import importlib
import time


def import_controller(asset_directory, selected_provider=None, **kwargs):
    """Imports a surface, atlas or object."""
    logging.debug("Importing asset...")
    logging.debug("Arguments: " + str(kwargs))
    ix = get_ix(kwargs.get("ix"))

    provider_names = PROVIDERS
    if selected_provider:
        provider_names = [PROVIDERS[PROVIDERS.index(selected_provider)]]

    asset = None
    for provider_name in provider_names:
        logging.debug("Checking if provider matches inspection: " + provider_name)
        provider = importlib.import_module('clarisse_survival_kit.providers.' + provider_name)
        report = provider.inspect_asset(asset_directory)
        if report:
            asset = provider.import_asset(asset_directory, report=report, **kwargs)
            break
        else:
            logging.debug('Provider %s did not pass inspection' % provider_name)
            if selected_provider:
                ix.log_warning('Content provider could not find asset in the specified directory.')
                return None
    return asset


def moisten_surface(ctx,
                    height_blend=True,
                    fractal_blend=False,
                    displacement_blend=False,
                    scope_blend=False,
                    slope_blend=False,
                    triplanar_blend=False,
                    ao_blend=False,
                    ior=MOISTURE_DEFAULT_IOR,
                    diffuse_multiplier=MOISTURE_DEFAULT_DIFFUSE_MULTIPLIER,
                    specular_multiplier=MOISTURE_DEFAULT_SPECULAR_MULTIPLIER,
                    roughness_multiplier=MOISTURE_DEFAULT_ROUGHNESS_MULTIPLIER,
                    **kwargs):
    """Moistens the selected material."""
    logging.debug("Moistening context: " + str(ctx))
    ix = get_ix(kwargs.get("ix"))
    if not check_context(ctx, ix=ix):
        return None
    surface_name = os.path.basename(str(ctx))
    ctx_members = get_items(ctx, ix=ix)

    mtl = None
    diffuse_tx = None
    specular_tx = None
    roughness_tx = None
    disp = None
    disp_tx = None
    for ctx_member in ctx_members:
        if ctx_member.get_contextual_name().endswith(DIFFUSE_SUFFIX):
            diffuse_tx = ctx_member
        if ctx_member.get_contextual_name().endswith(SPECULAR_COLOR_SUFFIX):
            specular_tx = ctx_member
        if ctx_member.get_contextual_name().endswith(SPECULAR_ROUGHNESS_SUFFIX):
            roughness_tx = ctx_member
        if ctx_member.is_kindof("MaterialPhysicalStandard"):
            if ctx_member.is_local() or not mtl:
                mtl = ctx_member
        if ctx_member.is_kindof("Displacement"):
            disp = ctx_member
        if ctx_member.get_contextual_name().endswith(DISPLACEMENT_SUFFIX):
            disp_tx = ctx_member
    if not mtl:
        logging.debug("No MaterialPhysicalStandard found in ctx")
        ix.log_warning("No MaterialPhysicalStandard found in context.")
        return False
    if not disp and not disp_tx and displacement_blend:
        logging.debug("No displacement found in ctx")
        ix.log_warning("No Displacement found in context. Cannot use Displacement blending.")
        return False
    elif not diffuse_tx or not specular_tx or not roughness_tx:
        logging.debug("No diffuse, specular or roughness found")
        ix.log_warning("Make sure the material has a diffuse, specular and roughness texture.")
        return False
    logging.debug("Creating selectors...")
    multi_blend_tx = ix.cmds.CreateObject(surface_name + MOISTURE_SUFFIX + MULTI_BLEND_SUFFIX, "TextureMultiBlend",
                                          "Global", str(ctx))

    selectors_ctx = ix.cmds.CreateContext(MOISTURE_CTX, "Global", str(ctx))
    # Setup fractal noise
    fractal_selector = create_fractal_selector(selectors_ctx, surface_name, MOISTURE_SUFFIX, ix=ix)

    # Setup slope gradient
    slope_selector = create_slope_selector(selectors_ctx, surface_name, MOISTURE_SUFFIX, ix=ix)

    # Setup scope
    scope_selector = create_scope_selector(selectors_ctx, surface_name, MOISTURE_SUFFIX, ix=ix)

    # Setup triplanar
    triplanar_selector = create_triplanar_selector(selectors_ctx, surface_name, MOISTURE_SUFFIX, ix=ix)

    # Setup AO
    ao_selector = create_ao_selector(selectors_ctx, surface_name, MOISTURE_SUFFIX, ix=ix)

    # Setup height blend
    height_selector = create_height_selector(selectors_ctx, surface_name, MOISTURE_SUFFIX, ix=ix, invert=True)

    disp_selector = None
    # Setup displacement blend
    if disp and disp_tx:
        disp_selector = create_displacement_selector(disp_tx, selectors_ctx, surface_name, "_moisture", ix=ix)

    logging.debug("Assigning selectors")
    multi_blend_tx.attrs.layer_1_label[0] = "Base intensity"
    # Attach Ambient Occlusion blend
    multi_blend_tx.attrs.enable_layer_2 = True
    multi_blend_tx.attrs.layer_2_mode = 1
    multi_blend_tx.attrs.layer_2_label[0] = "Ambient Occlusion Blend"
    ix.cmds.SetTexture([str(multi_blend_tx) + ".layer_2_color"], str(ao_selector))
    if not ao_blend: multi_blend_tx.attrs.enable_layer_2 = False
    # Attach displacement blend
    if disp_selector:
        multi_blend_tx.attrs.enable_layer_3 = True
        multi_blend_tx.attrs.layer_3_label[0] = "Displacement Blend"
        multi_blend_tx.attrs.layer_3_mode = 1
        ix.cmds.SetTexture([str(multi_blend_tx) + ".layer_3_color"], str(disp_selector))
        if not displacement_blend: multi_blend_tx.attrs.enable_layer_3 = False
    # Attach height blend
    multi_blend_tx.attrs.enable_layer_4 = True
    multi_blend_tx.attrs.layer_4_mode = 1
    multi_blend_tx.attrs.layer_4_label[0] = "Height Blend"
    ix.cmds.SetTexture([str(multi_blend_tx) + ".layer_4_color"], str(height_selector))
    if not height_blend: multi_blend_tx.attrs.enable_layer_4 = False
    # Attach slope blend
    multi_blend_tx.attrs.enable_layer_5 = True
    multi_blend_tx.attrs.layer_5_mode = 1
    multi_blend_tx.attrs.layer_5_label[0] = "Slope Blend"
    ix.cmds.SetTexture([str(multi_blend_tx) + ".layer_5_color"], str(slope_selector))
    if not slope_blend: multi_blend_tx.attrs.enable_layer_5 = False
    # Attach triplanar blend
    multi_blend_tx.attrs.enable_layer_6 = True
    multi_blend_tx.attrs.layer_6_mode = 1
    multi_blend_tx.attrs.layer_6_label[0] = "Triplanar Blend"
    ix.cmds.SetTexture([str(multi_blend_tx) + ".layer_6_color"], str(triplanar_selector))
    if not triplanar_blend: multi_blend_tx.attrs.enable_layer_6 = False
    # Attach scope blend
    multi_blend_tx.attrs.enable_layer_7 = True
    multi_blend_tx.attrs.layer_7_mode = 1
    multi_blend_tx.attrs.layer_7_label[0] = "Scope Blend"
    ix.cmds.SetTexture([str(multi_blend_tx) + ".layer_7_color"], str(scope_selector))
    if not scope_blend: multi_blend_tx.attrs.enable_layer_7 = False
    # Attach fractal blend
    multi_blend_tx.attrs.enable_layer_8 = True
    multi_blend_tx.attrs.layer_8_label[0] = "Fractal Blend"
    multi_blend_tx.attrs.layer_8_mode = 4 if True in [ao_blend, height_blend, slope_blend, scope_blend] else 1
    ix.cmds.SetTexture([str(multi_blend_tx) + ".layer_8_color"], str(fractal_selector))
    if not fractal_blend: multi_blend_tx.attrs.enable_layer_8 = False

    # Setup diffuse blend
    logging.debug("Setup diffuse blend")
    sub_ctx = get_sub_contexts(ctx, name='diffuse', ix=ix)
    diffuse_ctx = sub_ctx if sub_ctx else ctx

    diffuse_blend_tx = ix.cmds.CreateObject(surface_name + MOISTURE_DIFFUSE_BLEND_SUFFIX, "TextureBlend", "Global",
                                            str(diffuse_ctx))
    diffuse_blend_tx.attrs.input1[0] = diffuse_multiplier
    diffuse_blend_tx.attrs.input1[1] = diffuse_multiplier
    diffuse_blend_tx.attrs.input1[2] = diffuse_multiplier
    diffuse_blend_tx.attrs.mode = 7
    ix.cmds.SetTexture([str(diffuse_blend_tx) + ".mix"], str(multi_blend_tx))

    replace_connections(diffuse_blend_tx, diffuse_tx, ignored_attributes=['runtime_materials', ], ix=ix)
    ix.cmds.SetTexture([str(diffuse_blend_tx) + ".input2"], str(diffuse_tx))

    # Setup specular blend
    logging.debug("Setup specular blend")
    sub_ctx = get_sub_contexts(ctx, name='specular', ix=ix)
    specular_ctx = sub_ctx if sub_ctx else ctx
    specular_blend_tx = ix.cmds.CreateObject(surface_name + MOISTURE_SPECULAR_BLEND_SUFFIX, "TextureBlend", "Global",
                                             str(specular_ctx))
    ix.cmds.SetTexture([str(specular_blend_tx) + ".mix"], str(multi_blend_tx))
    specular_blend_tx.attrs.input1[0] = specular_multiplier
    specular_blend_tx.attrs.input1[1] = specular_multiplier
    specular_blend_tx.attrs.input1[2] = specular_multiplier
    specular_blend_tx.attrs.mode = 8

    replace_connections(specular_blend_tx, specular_tx, ignored_attributes=['runtime_materials', ], ix=ix)
    ix.cmds.SetTexture([str(specular_blend_tx) + ".input2"], str(specular_tx))

    # Setup roughness blend
    logging.debug("Setup roughness blend")
    sub_ctx = get_sub_contexts(ctx, name='roughness', ix=ix)
    roughness_ctx = sub_ctx if sub_ctx else ctx
    roughness_blend_tx = ix.cmds.CreateObject(surface_name + MOISTURE_ROUGHNESS_BLEND_SUFFIX, "TextureBlend", "Global",
                                              str(roughness_ctx))
    ix.cmds.SetTexture([str(roughness_blend_tx) + ".mix"], str(multi_blend_tx))
    roughness_blend_tx.attrs.input1[0] = roughness_multiplier
    roughness_blend_tx.attrs.input1[1] = roughness_multiplier
    roughness_blend_tx.attrs.input1[2] = roughness_multiplier
    roughness_blend_tx.attrs.mode = 7

    replace_connections(roughness_blend_tx, roughness_tx, ignored_attributes=['runtime_materials', ], ix=ix)
    ix.cmds.SetTexture([str(roughness_blend_tx) + ".input2"], str(roughness_tx))

    # Setup IOR blend
    ior_ctx = get_sub_contexts(ctx, name='ior', ix=ix)
    if not ior_ctx:
        ior_ctx = ix.cmds.CreateContext('ior', "Global", str(ctx))
    ior_tx = ix.cmds.CreateObject(surface_name + MOISTURE_IOR_BLEND_SUFFIX, "TextureBlend", "Global", str(ior_ctx))
    ior_tx.attrs.input2[0] = DEFAULT_IOR
    ior_tx.attrs.input2[1] = DEFAULT_IOR
    ior_tx.attrs.input2[2] = DEFAULT_IOR
    ior_tx.attrs.input1[0] = ior
    ior_tx.attrs.input1[1] = ior
    ior_tx.attrs.input1[2] = ior
    ix.cmds.SetTexture([str(ior_tx) + ".mix"], str(multi_blend_tx))
    logging.debug("Attaching IOR")
    ix.cmds.SetTexture([str(mtl) + ".specular_1_index_of_refraction"], str(ior_tx))
    logging.debug("Done moistening!!!")


def tint_surface(ctx, color, strength=.5, **kwargs):
    """
    Tints the diffuse texture with the specified color
    """
    logging.debug("Tint surface started")
    ix = get_ix(kwargs.get("ix"))
    if not check_context(ctx, ix=ix):
        return None

    ctx_members = get_items(ctx, ix=ix)
    surface_name = os.path.basename(str(ctx))
    mtl = None
    for ctx_member in ctx_members:
        if ctx_member.is_kindof("MaterialPhysicalStandard"):
            if ctx_member.is_local() or not mtl:
                mtl = ctx_member
    if not mtl:
        ix.log_warning("No valid material or displacement found.")
        return False

    diffuse_tx = ix.get_item(str(mtl) + '.diffuse_front_color').get_texture()
    if diffuse_tx:
        sub_ctx = get_sub_contexts(ctx, name='diffuse', ix=ix)
        target_ctx = sub_ctx if sub_ctx else ctx
        tint_tx = ix.cmds.CreateObject(surface_name + DIFFUSE_TINT_SUFFIX, "TextureBlend", "Global", str(target_ctx))
        tint_tx.attrs.mix = strength
        tint_tx.attrs.mode = 12
        tint_tx.attrs.input1[0] = color[0]
        tint_tx.attrs.input1[1] = color[1]
        tint_tx.attrs.input1[2] = color[2]
        ix.cmds.SetTexture([str(tint_tx) + ".input2"], str(diffuse_tx))
        ix.cmds.SetTexture([str(mtl) + ".diffuse_front_color"], str(tint_tx))
        logging.debug("Tint succeeded!!!")
        return tint_tx
    else:
        ix.log_warning("No textures assigned to diffuse channel.")
        logging.debug("No textures assigned to diffuse channel.")
        return None


def replace_surface(ctx, surface_directory, selected_provider=None, **kwargs):
    """
    Replace the selected surface context with a different surface.
    Links between blend materials are maintained.
    """
    logging.debug("Replace surface called...")
    logging.debug("Arguments: " + str(kwargs))
    ix = get_ix(kwargs.get("ix"))
    if not check_context(ctx, ix=ix):
        return None

    provider_names = PROVIDERS
    if selected_provider:
        provider_names = [PROVIDERS[PROVIDERS.index(selected_provider)]]

    uv_scale = DEFAULT_UV_SCALE
    surface_height = DEFAULT_DISPLACEMENT_HEIGHT
    displacement_offset = DEFAULT_DISPLACEMENT_OFFSET
    tileable = True
    color_spaces = kwargs.get('color_spaces', DEFAULT_COLOR_SPACES)
    clip_opacity = kwargs.get('clip_opacity', True)
    ior = kwargs.get('ior', DEFAULT_IOR)
    metallic_ior = kwargs.get('metallic_ior', DEFAULT_METALLIC_IOR)
    surface_name = os.path.basename(os.path.dirname(os.path.join(surface_directory, '')))
    object_space = kwargs.get('object_space', 0)
    triplanar_blend = kwargs.get('triplanar_blend', 0.5)
    projection_type = kwargs.get('projection_type', 'triplanar')

    for provider_name in provider_names:
        logging.debug("Checking if provider matches inspection: " + provider_name)
        provider = importlib.import_module('clarisse_survival_kit.providers.' + provider_name)
        report = provider.inspect_asset(surface_directory)
        if report:
            if report.get('scan_area'):
                uv_scale = report.get('scan_area')
            if report.get('tileable'):
                tileable = report.get('tileable')
            break
        else:
            logging.debug('Provider %s did not pass inspection' % provider_name)
            if selected_provider:
                ix.log_warning('Content provider could not find asset in the specified directory.')
                return None
    if uv_scale[0] >= 2 and uv_scale[1] >= 2:
        surface_height = 0.2
    else:
        surface_height = 0.02

    surface_directory = os.path.normpath(surface_directory)
    if not os.path.isdir(surface_directory):
        return ix.log_warning("Invalid directory specified: " + surface_directory)
    logging.debug("Surface directory:" + surface_directory)

    # Let's find the textures
    textures = get_textures_from_directory(surface_directory)
    streamed_maps = get_stream_map_files(textures)
    if not textures:
        ix.log_warning("No textures found in directory.")
        return False

    surface = Surface(ix)
    surface.load(ctx)
    update_textures = {}
    for key, tx in surface.textures.copy().iteritems():
        if tx.is_kindof('TextureMapFile') or tx.is_kindof('TextureStreamedMapFile'):
            # Swap filename
            if key in textures:
                print "UPDATING FROM SURFACE: " + key
                logging.debug("Texture needing update: " + key)
                update_textures[key] = textures.get(key)
            elif key not in textures:
                print "DELETING FROM SURFACE: " + key
                logging.debug("Texture no longer needed: " + key)
                surface.destroy_tx(key)
    new_textures = {}
    for key, tx in textures.iteritems():
        if key not in surface.textures:
            print "NOT IN SURFACE: " + key
            logging.debug("New texture: " + key)
            new_textures[key] = tx

    surface.create_textures(new_textures, color_spaces=color_spaces, streamed_maps=streamed_maps,
                            clip_opacity=clip_opacity)
    surface.update_ior(ior, metallic_ior=metallic_ior)
    surface.update_textures(update_textures, color_spaces=color_spaces, streamed_maps=streamed_maps)
    surface.update_names(surface_name)
    surface.update_displacement(surface_height, displacement_offset=displacement_offset)
    surface.update_opacity(clip_opacity=clip_opacity, found_textures=textures, update_textures=update_textures)
    surface.update_projection(projection=projection_type, uv_scale=uv_scale,
                              triplanar_blend=triplanar_blend, object_space=object_space, tile=True)
    surface.clean()
    return surface


def mix_surfaces(srf_ctxs, cover_ctx, mode="create", mix_name="mix" + MATERIAL_SUFFIX,
                 target_context=None, displacement_blend=True, height_blend=False,
                 ao_blend=False, fractal_blend=True, triplanar_blend=True,
                 slope_blend=True, scope_blend=True, assign_mtls=True, **kwargs):
    """Mixes one or multiple surfaces with a cover surface."""
    ix = get_ix(kwargs.get("ix"))
    if not target_context:
        target_context = ix.application.get_working_context()
    if not check_context(target_context, ix=ix):
        return None
    print "Mixing surfaces"
    logging.debug("Mixing surfaces...")

    if mode == 'create':
        root_ctx = ix.cmds.CreateContext(mix_name, "Global", str(target_context))
        selectors_ctx = ix.cmds.CreateContext(MIX_SELECTORS_NAME, "Global", str(root_ctx))

        cover_mtl = get_mtl_from_context(cover_ctx, ix=ix)
        cover_disp = get_disp_from_context(cover_ctx, ix=ix)
        cover_name = cover_ctx.get_name()
        logging.debug("Cover mtl: " + cover_name)
        logging.debug("Setting up common selectors...")
        # Setup all common selectors
        # Setup fractal noise
        fractal_selector = create_fractal_selector(selectors_ctx, mix_name, MIX_SUFFIX, ix=ix)

        # Setup slope gradient
        slope_selector = create_slope_selector(selectors_ctx, mix_name, MIX_SUFFIX, ix=ix)

        # Setup scope
        scope_selector = create_scope_selector(selectors_ctx, mix_name, MIX_SUFFIX, ix=ix)

        # Setup triplanar
        triplanar_selector = create_triplanar_selector(selectors_ctx, mix_name, MIX_SUFFIX, ix=ix)

        # Setup AO
        ao_selector = create_ao_selector(selectors_ctx, mix_name, MIX_SUFFIX, ix=ix)

        # Setup height blend
        height_selector = create_height_selector(selectors_ctx, mix_name, MIX_SUFFIX, ix=ix)

        # Put all selectors in a TextureMultiBlend
        logging.debug("Generate master multi blend and attach selectors: ")
        multi_blend_tx = ix.cmds.CreateObject(mix_name + MULTI_BLEND_SUFFIX, "TextureMultiBlend",
                                              "Global", str(root_ctx))
        multi_blend_tx.attrs.layer_1_label[0] = "Base intensity"
        # Attach displacement blend
        multi_blend_tx.attrs.enable_layer_2 = True
        multi_blend_tx.attrs.layer_2_label[0] = "Displacement Blend"
        multi_blend_tx.attrs.layer_2_mode = 1
        # Attach Ambient Occlusion blend
        multi_blend_tx.attrs.enable_layer_3 = True
        multi_blend_tx.attrs.layer_3_mode = 1
        multi_blend_tx.attrs.layer_3_label[0] = "Ambient Occlusion Blend"
        ix.cmds.SetTexture([str(multi_blend_tx) + ".layer_3_color"], str(ao_selector))
        if not ao_blend: multi_blend_tx.attrs.enable_layer_3 = False
        # Attach height blend
        multi_blend_tx.attrs.enable_layer_4 = True
        multi_blend_tx.attrs.layer_4_mode = 1
        multi_blend_tx.attrs.layer_4_label[0] = "Height Blend"
        ix.cmds.SetTexture([str(multi_blend_tx) + ".layer_4_color"], str(height_selector))
        if not height_blend: multi_blend_tx.attrs.enable_layer_4 = False
        # Attach slope blend
        multi_blend_tx.attrs.enable_layer_5 = True
        multi_blend_tx.attrs.layer_5_mode = 1
        multi_blend_tx.attrs.layer_5_label[0] = "Slope Blend"
        ix.cmds.SetTexture([str(multi_blend_tx) + ".layer_5_color"], str(slope_selector))
        if not slope_blend: multi_blend_tx.attrs.enable_layer_5 = False
        # Attach triplanar blend
        multi_blend_tx.attrs.enable_layer_6 = True
        multi_blend_tx.attrs.layer_6_mode = 1
        multi_blend_tx.attrs.layer_6_label[0] = "Triplanar Blend"
        ix.cmds.SetTexture([str(multi_blend_tx) + ".layer_6_color"], str(triplanar_selector))
        if not triplanar_blend: multi_blend_tx.attrs.enable_layer_6 = False
        # Attach scope blend
        multi_blend_tx.attrs.enable_layer_7 = True
        multi_blend_tx.attrs.layer_7_mode = 1
        multi_blend_tx.attrs.layer_7_label[0] = "Scope Blend"
        ix.cmds.SetTexture([str(multi_blend_tx) + ".layer_7_color"], str(scope_selector))
        if not scope_blend: multi_blend_tx.attrs.enable_layer_7 = False
        # Attach fractal blend
        multi_blend_tx.attrs.enable_layer_8 = True
        multi_blend_tx.attrs.layer_8_label[0] = "Fractal Blend"
        multi_blend_tx.attrs.layer_8_mode = 4 if True in [ao_blend, height_blend, slope_blend, scope_blend] else 1
        ix.cmds.SetTexture([str(multi_blend_tx) + ".layer_8_color"], str(fractal_selector))
        if not fractal_blend: multi_blend_tx.attrs.enable_layer_8 = False
    elif mode == 'add':
        root_ctx = cover_ctx
        previous_blend_mtl = get_items(root_ctx, kind=['MaterialPhysicalBlend'], return_first_hit=True, ix=ix)
        multi_blend_tx = get_items(root_ctx, kind=['TextureMultiBlend'], return_first_hit=True, max_depth=1, ix=ix)
        if not previous_blend_mtl:
            print "ERROR: Couldn't find blend material."
            logging.error("Couldn't find blend material.")
            return None
        cover_mtl = previous_blend_mtl.attrs.input1.attr.get_object()
        cover_ctx = cover_mtl.get_context()
        cover_name = cover_ctx.get_name()
        cover_disp = get_items(cover_ctx, kind=['Displacement'], return_first_hit=True, ix=ix)
    else:
        logging.error("Can only create or add to mix.")
        return None

    # Set up each surface mix
    for srf_ctx in srf_ctxs:
        mix_srf_name = srf_ctx.get_name()
        logging.debug("Generating mix of base surface: " + mix_srf_name)
        mix_ctx = ix.cmds.CreateContext(mix_srf_name + MIX_SUFFIX, "Global", str(root_ctx))
        mix_selectors_ctx = ix.cmds.CreateContext("custom_selectors", "Global", str(mix_ctx))

        base_mtl = get_mtl_from_context(srf_ctx, ix=ix)
        base_disp = get_disp_from_context(srf_ctx, ix=ix)

        has_displacement = base_disp and cover_disp

        mix_multi_blend_tx = ix.cmds.Instantiate([str(multi_blend_tx)])[0]
        ix.cmds.MoveItemsTo([str(mix_multi_blend_tx)], mix_selectors_ctx)
        ix.cmds.RenameItem(str(mix_multi_blend_tx), mix_srf_name + MULTI_BLEND_SUFFIX)
        # Blend materials
        mix_mtl = ix.cmds.CreateObject(mix_srf_name + MIX_SUFFIX + MATERIAL_SUFFIX, "MaterialPhysicalBlend", "Global",
                                       str(mix_ctx))
        ix.cmds.SetTexture([str(mix_mtl) + ".mix"], str(mix_multi_blend_tx))
        ix.cmds.SetValue(str(mix_mtl) + ".input2", [str(base_mtl)])
        ix.cmds.SetValue(str(mix_mtl) + ".input1", [str(cover_mtl)])

        mix_disp = ''
        if has_displacement:
            logging.debug("Surface has displacement. Setting up unique selector...")
            ix.cmds.LocalizeAttributes([str(mix_multi_blend_tx) + ".layer_2_color",
                                        str(mix_multi_blend_tx) + ".enable_layer_2"], True)
            # Setup displacements for height blending.
            # Base surface
            print "Setting up surface 1"
            base_srf_height = base_disp.attrs.front_value[0]
            base_disp_blend_offset_tx = ix.cmds.CreateObject(mix_srf_name + DISPLACEMENT_BLEND_OFFSET_SUFFIX,
                                                             "TextureAdd", "Global", str(mix_selectors_ctx))
            base_disp_tx_front_value = ix.get_item(str(base_disp) + ".front_value")
            base_disp_tx = base_disp_tx_front_value.get_texture()
            legacy_mode = False
            if base_srf_height != 1:
                print "Base surface height: " + str(base_srf_height)
                base_disp_height_scale_tx = ix.cmds.CreateObject(mix_srf_name + DISPLACEMENT_HEIGHT_SCALE_SUFFIX,
                                                                 "TextureMultiply", "Global", str(mix_selectors_ctx))
                ix.cmds.SetTexture([str(base_disp_height_scale_tx) + ".input1"], str(base_disp_tx))

                base_disp_height_scale_tx.attrs.input2[0] = base_srf_height
                base_disp_height_scale_tx.attrs.input2[1] = base_srf_height
                base_disp_height_scale_tx.attrs.input2[2] = base_srf_height
                ix.cmds.SetTexture([str(base_disp_blend_offset_tx) + ".input1"], str(base_disp_height_scale_tx))
                base_disp_offset_tx = ix.cmds.CreateObject(mix_srf_name + DISPLACEMENT_OFFSET_SUFFIX, "TextureAdd",
                                                           "Global", str(mix_selectors_ctx))
                base_disp_offset_tx.attrs.input2[0] = -0.5 * base_srf_height + 0.5
                base_disp_offset_tx.attrs.input2[1] = -0.5 * base_srf_height + 0.5
                base_disp_offset_tx.attrs.input2[2] = -0.5 * base_srf_height + 0.5
                ix.cmds.SetTexture([str(base_disp_offset_tx) + ".input1"], str(base_disp_height_scale_tx))
                legacy_mode = True
            else:
                base_disp_blend_offset_tx.attrs.input2[0] = 1
                base_disp_blend_offset_tx.attrs.input2[1] = 1
                base_disp_blend_offset_tx.attrs.input2[2] = 1
                ix.cmds.SetTexture([str(base_disp_blend_offset_tx) + ".input1"], str(base_disp_tx))
                base_disp_offset_tx = base_disp_tx

            # Surface 2
            print "Setting up surface 2"
            cover_srf_height = cover_disp.attrs.front_value[0]

            cover_disp_blend_offset_tx = ix.cmds.CreateObject(cover_name + DISPLACEMENT_BLEND_OFFSET_SUFFIX,
                                                              "TextureAdd", "Global", str(mix_selectors_ctx))
            cover_disp_tx_front_value = ix.get_item(str(cover_disp) + ".front_value")
            cover_disp_tx = cover_disp_tx_front_value.get_texture()
            if cover_srf_height != 1:
                print "Surface 2 height: " + str(cover_srf_height)
                cover_disp_height_scale_tx = ix.cmds.CreateObject(cover_name + DISPLACEMENT_HEIGHT_SCALE_SUFFIX,
                                                                  "TextureMultiply", "Global", str(mix_selectors_ctx))
                ix.cmds.SetTexture([str(cover_disp_height_scale_tx) + ".input1"], str(cover_disp_tx))
                cover_disp_height_scale_tx.attrs.input2[0] = cover_srf_height
                cover_disp_height_scale_tx.attrs.input2[1] = cover_srf_height
                cover_disp_height_scale_tx.attrs.input2[2] = cover_srf_height
                ix.cmds.SetTexture([str(cover_disp_blend_offset_tx) + ".input1"], str(cover_disp_height_scale_tx))
                cover_disp_offset_tx = ix.cmds.CreateObject(cover_name + DISPLACEMENT_OFFSET_SUFFIX, "TextureAdd",
                                                            "Global", str(mix_selectors_ctx))
                cover_disp_offset_tx.attrs.input2[0] = -0.5 * cover_srf_height + 0.5
                cover_disp_offset_tx.attrs.input2[1] = -0.5 * cover_srf_height + 0.5
                cover_disp_offset_tx.attrs.input2[2] = -0.5 * cover_srf_height + 0.5
                ix.cmds.SetTexture([str(cover_disp_offset_tx) + ".input1"], str(cover_disp_height_scale_tx))
                legacy_mode = True
            else:
                cover_disp_blend_offset_tx.attrs.input2[0] = 1
                cover_disp_blend_offset_tx.attrs.input2[1] = 1
                cover_disp_blend_offset_tx.attrs.input2[2] = 1
                ix.cmds.SetTexture([str(cover_disp_blend_offset_tx) + ".input1"], str(cover_disp_tx))
                cover_disp_offset_tx = cover_disp_tx

            disp_branch_selector = ix.cmds.CreateObject(mix_srf_name + DISPLACEMENT_BRANCH_SUFFIX, "TextureBranch",
                                                        "Global", str(mix_selectors_ctx))

            ix.cmds.SetTexture([str(disp_branch_selector) + ".input_a"], str(base_disp_blend_offset_tx))
            ix.cmds.SetTexture([str(disp_branch_selector) + ".input_b"], str(cover_disp_blend_offset_tx))
            disp_branch_selector.attrs.mode = 2

            # Hook to multiblend instance
            ix.cmds.SetTexture([str(mix_multi_blend_tx) + ".layer_2_color"], str(disp_branch_selector))
            if not displacement_blend: mix_multi_blend_tx.attrs.enable_layer_2 = False
            # Finalize new Displacement map
            disp_multi_blend_tx = ix.cmds.CreateObject(mix_srf_name + DISPLACEMENT_BLEND_SUFFIX,
                                                       "TextureMultiBlend", "Global", str(mix_selectors_ctx))
            ix.cmds.SetTexture([str(disp_multi_blend_tx) + ".layer_1_color"], str(base_disp_offset_tx))
            disp_multi_blend_tx.attrs.enable_layer_2 = True
            disp_multi_blend_tx.attrs.layer_2_label[0] = "Mix mode"
            ix.cmds.SetTexture([str(disp_multi_blend_tx) + ".layer_2_color"], str(cover_disp_offset_tx))
            ix.cmds.SetTexture([str(disp_multi_blend_tx) + ".layer_2_mix"], str(mix_multi_blend_tx))
            disp_multi_blend_tx.attrs.enable_layer_3 = True
            disp_multi_blend_tx.attrs.layer_3_label[0] = "Add mode"
            ix.cmds.SetTexture([str(disp_multi_blend_tx) + ".layer_3_color"], str(cover_disp_offset_tx))
            ix.cmds.SetTexture([str(disp_multi_blend_tx) + ".layer_3_mix"], str(mix_multi_blend_tx))
            disp_multi_blend_tx.attrs.layer_3_mode = 6
            disp_multi_blend_tx.attrs.enable_layer_3 = False

            mix_disp = ix.cmds.CreateObject(mix_srf_name + DISPLACEMENT_MAP_SUFFIX, "Displacement",
                                            "Global",
                                            str(mix_ctx))
            mix_disp.attrs.bound[0] = 1
            mix_disp.attrs.bound[1] = 1
            mix_disp.attrs.bound[2] = 1
            mix_disp.attrs.front_value = 1
            if legacy_mode:
                mix_disp.attrs.front_offset = -0.5
            ix.cmds.SetTexture([str(mix_disp) + ".front_value"], str(disp_multi_blend_tx))
        if assign_mtls:
            mtls = get_all_mtls_from_context(srf_ctx, ix=ix)
            for mtl in mtls:
                logging.debug("Material assignment...")
                ix.selection.deselect_all()
                ix.application.check_for_events()
                ix.selection.select(mtl)
                ix.application.select_next_outputs()
                selection = [i for i in ix.selection]
                for sel in selection:
                    if sel.is_kindof("Geometry"):
                        shading_group = sel.get_module().get_geometry().get_shading_group_names()
                        count = shading_group.get_count()
                        for j in range(count):
                            shader = sel.attrs.materials[j]
                            if shader == mtl:
                                ix.cmds.SetValues([str(sel) + ".materials" + str([j])], [str(mix_mtl)])
                            if has_displacement:
                                if sel.attrs.displacements[j] == base_disp:
                                    ix.cmds.SetValues([str(sel) + ".displacements" + str([j])], [str(mix_disp)])
                ix.selection.deselect_all()
                ix.application.check_for_events()
                logging.debug("... done material assignment.")
    logging.debug("Done mixing!!!")
    return root_ctx


def toggle_surface_complexity(ctx, **kwargs):
    """Temporarily replaces the current surface with a much simpeler MaterialPhysicalDiffuse material."""
    logging.debug("Toggle surface complexity...")
    ix = get_ix(kwargs.get("ix"))
    objects_array = ix.api.OfObjectArray(ctx.get_object_count())
    flags = ix.api.CoreBitFieldHelper()
    ctx.get_all_objects(objects_array, flags, False)
    surface_name = os.path.basename(str(ctx))

    mtl = None
    preview_mtl = None
    disp = None
    for ctx_member in objects_array:
        if ctx_member.is_kindof("MaterialPhysicalStandard"):
            if ctx_member.is_local() or not mtl:
                mtl = ctx_member
        if ctx_member.is_kindof("MaterialPhysicalBlend"):
            mtl = ctx_member
        if ctx_member.is_kindof("MaterialPhysicalDiffuse"):
            preview_mtl = ctx_member
        if ctx_member.is_kindof("Displacement"):
            disp = ctx_member
    if not mtl:
        ix.log_warning("No MaterialPhysicalStandard found in context.")
        ix.selection.deselect_all()
        return False
    if disp:
        # Disable the displacement
        ix.cmds.DisableItems([str(disp)], disp.is_enabled())
    if mtl.is_kindof("MaterialPhysicalBlend"):
        ix.selection.deselect_all()
        return True
    if not preview_mtl:
        logging.debug("Switching to simple mode...")
        diffuse_tx = ix.get_item(str(mtl) + '.diffuse_front_color').get_texture()
        new_preview_mtl = ix.cmds.CreateObject(surface_name + PREVIEW_MATERIAL_SUFFIX, "MaterialPhysicalDiffuse",
                                               "Global", str(ctx))
        ix.cmds.SetTexture([str(new_preview_mtl) + ".front_color"],
                           str(diffuse_tx))

        replace_connections(new_preview_mtl, mtl, ignored_attributes=['runtime_materials', ], ix=ix)
    else:
        logging.debug("Reverting back to complex mode...")
        replace_connections(mtl, preview_mtl, ignored_attributes=['runtime_materials', ], ix=ix)
        ix.cmds.DeleteItems([str(preview_mtl)])
    ix.selection.deselect_all()
    logging.debug("Done toggling surface complexity!!!")


def generate_decimated_pointcloud(geometry, ctx=None,
                                  pc_type="GeometryPointCloud",
                                  use_density=False,
                                  density=.1,
                                  point_count=10000,
                                  height_blend=False,
                                  fractal_blend=False,
                                  scope_blend=False,
                                  slope_blend=True,
                                  triplanar_blend=False,
                                  ao_blend=False,
                                  **kwargs):
    """Generates a pointcloud from the selected geometry."""
    logging.debug("Generating decimated pointcloud...")
    logging.debug("Type: " + pc_type)
    logging.debug("Use density: " + str(use_density))
    ix = get_ix(kwargs.get("ix"))
    if not ctx:
        ctx = ix.application.get_working_context()
    if not check_context(ctx, ix=ix):
        return None

    geo_name = geometry.get_contextual_name()
    pc_ctx = ix.cmds.CreateContext(POINTCLOUD_CTX, "Global", str(ctx))
    selectors_ctx = ix.cmds.CreateContext('selectors', "Global", str(pc_ctx))
    pc = ix.cmds.CreateObject(geo_name + POINTCLOUD_SUFFIX, pc_type, "Global", str(pc_ctx))
    ix.application.check_for_events()
    if pc_type == "GeometryPointCloud":
        if use_density:
            ix.cmds.SetValue(str(pc) + ".use_density", [str(1)])
            ix.application.check_for_events()
            ix.cmds.SetValue(str(pc) + ".density", [str(density)])
        else:
            pc.attrs.point_count = int(point_count)
    else:
        pc.attrs.point_count = int(point_count)

    logging.debug("Parenting...")
    ix.cmds.AddValues([str(pc) + ".constraints"], ["ConstraintParent"])
    ix.application.check_for_events()
    time.sleep(0.25)
    ix.cmds.SetValues([str(pc) + ".parent.target"], [str(geometry)])
    ix.application.check_for_events()
    logging.debug("Setting up multi blend and selectors...")
    multi_blend_tx = ix.cmds.CreateObject(geo_name + DECIMATE_SUFFIX + MULTI_BLEND_SUFFIX, "TextureMultiBlend",
                                          "Global", str(pc_ctx))
    # Setup fractal noise
    fractal_selector = create_fractal_selector(selectors_ctx, geo_name, DECIMATE_SUFFIX, ix=ix)

    # Setup slope gradient
    slope_selector = create_slope_selector(selectors_ctx, geo_name, DECIMATE_SUFFIX, ix=ix)

    # Setup scope
    scope_selector = create_scope_selector(selectors_ctx, geo_name, DECIMATE_SUFFIX, ix=ix)

    # Setup triplanar
    triplanar_selector = create_triplanar_selector(selectors_ctx, geo_name, DECIMATE_SUFFIX, ix=ix)

    # Setup AO
    ao_selector = create_ao_selector(selectors_ctx, geo_name, DECIMATE_SUFFIX, ix=ix)

    # Setup height blend
    height_selector = create_height_selector(selectors_ctx, geo_name, DECIMATE_SUFFIX, ix=ix)

    multi_blend_tx.attrs.layer_1_label[0] = "Base intensity"
    # Attach Ambient Occlusion blend
    multi_blend_tx.attrs.enable_layer_2 = True
    multi_blend_tx.attrs.layer_2_mode = 1
    multi_blend_tx.attrs.layer_2_label[0] = "Ambient Occlusion Blend"
    ix.cmds.SetTexture([str(multi_blend_tx) + ".layer_2_color"], str(ao_selector))
    if not ao_blend: multi_blend_tx.attrs.enable_layer_2 = False
    # Attach height blend
    multi_blend_tx.attrs.enable_layer_4 = True
    multi_blend_tx.attrs.layer_4_mode = 1
    multi_blend_tx.attrs.layer_4_label[0] = "Height Blend"
    ix.cmds.SetTexture([str(multi_blend_tx) + ".layer_4_color"], str(height_selector))
    if not height_blend: multi_blend_tx.attrs.enable_layer_4 = False
    # Attach slope blend
    multi_blend_tx.attrs.enable_layer_5 = True
    multi_blend_tx.attrs.layer_5_mode = 1
    multi_blend_tx.attrs.layer_5_label[0] = "Slope Blend"
    ix.cmds.SetTexture([str(multi_blend_tx) + ".layer_5_color"], str(slope_selector))
    if not slope_blend: multi_blend_tx.attrs.enable_layer_5 = False
    # Attach triplanar blend
    multi_blend_tx.attrs.enable_layer_6 = True
    multi_blend_tx.attrs.layer_6_mode = 1
    multi_blend_tx.attrs.layer_6_label[0] = "Triplanar Blend"
    ix.cmds.SetTexture([str(multi_blend_tx) + ".layer_6_color"], str(triplanar_selector))
    if not triplanar_blend: multi_blend_tx.attrs.enable_layer_6 = False
    # Attach scope blend
    multi_blend_tx.attrs.enable_layer_7 = True
    multi_blend_tx.attrs.layer_7_mode = 1
    multi_blend_tx.attrs.layer_7_label[0] = "Scope Blend"
    ix.cmds.SetTexture([str(multi_blend_tx) + ".layer_7_color"], str(scope_selector))
    if not scope_blend: multi_blend_tx.attrs.enable_layer_7 = False
    # Attach fractal blend
    multi_blend_tx.attrs.enable_layer_8 = True
    multi_blend_tx.attrs.layer_8_label[0] = "Fractal Blend"
    multi_blend_tx.attrs.layer_8_mode = 4 if True in [ao_blend, height_blend, slope_blend, scope_blend] else 1
    ix.cmds.SetTexture([str(multi_blend_tx) + ".layer_8_color"], str(fractal_selector))
    if not fractal_blend: multi_blend_tx.attrs.enable_layer_8 = False

    if pc_type == "GeometryPointCloud":
        ix.cmds.SetValue(str(pc) + ".decimate_texture", [str(multi_blend_tx)])
        ix.cmds.SetValue(str(multi_blend_tx) + ".invert", [str(1)])
    else:
        ix.cmds.SetValue(str(pc) + ".texture", [str(multi_blend_tx)])

    ix.cmds.SetValue(str(pc) + ".geometry", [str(geometry)])
    logging.debug("Done generating point cloud!!!")
    return pc


def mask_blend_nodes(blend_nodes, ctx=None, mix_name='mix',
                     height_blend=False,
                     fractal_blend=False,
                     scope_blend=False,
                     slope_blend=True,
                     triplanar_blend=False,
                     ao_blend=False,
                     **kwargs):
    """Generates masks on the selected blend textures/materials."""
    logging.debug("Masking blend items...")
    ix = get_ix(kwargs.get("ix"))
    if not ctx:
        ctx = ix.application.get_working_context()
    if not check_context(ctx, ix=ix):
        return None

    selectors_ctx = ix.cmds.CreateContext(MIX_SELECTORS_NAME, "Global", str(ctx))

    multi_blend_tx = ix.cmds.CreateObject(mix_name + MULTI_BLEND_SUFFIX, "TextureMultiBlend",
                                          "Global", str(ctx))
    # Setup fractal noise
    fractal_selector = create_fractal_selector(selectors_ctx, mix_name, MIX_SUFFIX, ix=ix)

    # Setup slope gradient
    slope_selector = create_slope_selector(selectors_ctx, mix_name, MIX_SUFFIX, ix=ix)

    # Setup scope
    scope_selector = create_scope_selector(selectors_ctx, mix_name, MIX_SUFFIX, ix=ix)

    # Setup triplanar
    triplanar_selector = create_triplanar_selector(selectors_ctx, mix_name, MIX_SUFFIX, ix=ix)

    # Setup AO
    ao_selector = create_ao_selector(selectors_ctx, mix_name, MIX_SUFFIX, ix=ix)

    # Setup height blend
    height_selector = create_height_selector(selectors_ctx, mix_name, MIX_SUFFIX, ix=ix)

    multi_blend_tx.attrs.layer_1_label[0] = "Base intensity"
    # Attach Ambient Occlusion blend
    multi_blend_tx.attrs.enable_layer_2 = True
    multi_blend_tx.attrs.layer_2_mode = 1
    multi_blend_tx.attrs.layer_2_label[0] = "Ambient Occlusion Blend"
    ix.cmds.SetTexture([str(multi_blend_tx) + ".layer_2_color"], str(ao_selector))
    if not ao_blend: multi_blend_tx.attrs.enable_layer_2 = False
    # Attach height blend
    multi_blend_tx.attrs.enable_layer_4 = True
    multi_blend_tx.attrs.layer_4_mode = 1
    multi_blend_tx.attrs.layer_4_label[0] = "Height Blend"
    ix.cmds.SetTexture([str(multi_blend_tx) + ".layer_4_color"], str(height_selector))
    if not height_blend: multi_blend_tx.attrs.enable_layer_4 = False
    # Attach slope blend
    multi_blend_tx.attrs.enable_layer_5 = True
    multi_blend_tx.attrs.layer_5_mode = 1
    multi_blend_tx.attrs.layer_5_label[0] = "Slope Blend"
    ix.cmds.SetTexture([str(multi_blend_tx) + ".layer_5_color"], str(slope_selector))
    if not slope_blend: multi_blend_tx.attrs.enable_layer_5 = False
    # Attach triplanar blend
    multi_blend_tx.attrs.enable_layer_6 = True
    multi_blend_tx.attrs.layer_6_mode = 1
    multi_blend_tx.attrs.layer_6_label[0] = "Triplanar Blend"
    ix.cmds.SetTexture([str(multi_blend_tx) + ".layer_6_color"], str(triplanar_selector))
    if not triplanar_blend: multi_blend_tx.attrs.enable_layer_6 = False
    # Attach scope blend
    multi_blend_tx.attrs.enable_layer_7 = True
    multi_blend_tx.attrs.layer_7_mode = 1
    multi_blend_tx.attrs.layer_7_label[0] = "Scope Blend"
    ix.cmds.SetTexture([str(multi_blend_tx) + ".layer_7_color"], str(scope_selector))
    if not scope_blend: multi_blend_tx.attrs.enable_layer_7 = False
    # Attach fractal blend
    multi_blend_tx.attrs.enable_layer_8 = True
    multi_blend_tx.attrs.layer_8_label[0] = "Fractal Blend"
    multi_blend_tx.attrs.layer_8_mode = 4 if True in [ao_blend, height_blend, slope_blend, scope_blend] else 1
    ix.cmds.SetTexture([str(multi_blend_tx) + ".layer_8_color"], str(fractal_selector))
    if not fractal_blend: multi_blend_tx.attrs.enable_layer_8 = False

    for blend_node in blend_nodes:
        ix.cmds.SetTexture([str(blend_node) + ".mix"], str(multi_blend_tx))

    logging.debug("Done adding selectors!!!")
    return multi_blend_tx


def create_tiled_terrain(divisions_x, divisions_y, ctx=None, tile_flip_x=False, tile_flip_y=False,
                         tile_pattern=r".*_x(?P<tile_x>\d+)_y(?P<tile_y>\d+)\.", **kwargs):
    """Generates a tiled displaced terrain from the selected heightmap."""
    logging.debug("Generating tiled terrain...")
    ix = get_ix(kwargs.get("ix"))
    if not ctx:
        ctx = ix.application.get_working_context()
    if not check_context(ctx, ix=ix):
        return None

    heightmap_file = kwargs.pop('heightmap_file')
    terrain_name = kwargs.pop('terrain_name')
    terrain_ctx = ix.cmds.CreateContext(terrain_name, "Global", str(ctx))

    dimensions = kwargs.pop('dimensions', (2048, 2048, 400))
    terrain_width = float(dimensions[0])
    terrain_length = float(dimensions[1])

    directory, filename = os.path.split(heightmap_file)
    multi_file_match = re.search(tile_pattern, r"{}".format(filename), re.IGNORECASE)
    tiles = []
    if multi_file_match:
        glob_filename = re.sub(tile_pattern, r"*", r"{}".format(filename))
        terrain_files = glob.glob(os.path.join(directory, glob_filename))
        # Check the amount of tile divisions in X and Y
        divisions_x = 0
        divisions_y = 0
        for terrain_file in terrain_files:
            tile_match = re.search(tile_pattern, r"{}".format(terrain_file), re.IGNORECASE)
            if tile_match:
                tile_x = int(tile_match.group('tile_x'))
                if tile_x > divisions_x:
                    divisions_x = tile_x
                tile_y = int(tile_match.group('tile_y'))
                if tile_y > divisions_y:
                    divisions_y = tile_y
        # Because they start at 0 we must add 1
        divisions_x += 1
        divisions_y += 1

        tile_width = float(dimensions[0]) / float(divisions_x)
        tile_length = float(dimensions[1]) / float(divisions_y)
        tile_dimensions = (tile_width, tile_length, dimensions[2])

        for terrain_file in terrain_files:
            tile_match = re.search(tile_pattern, r"{}".format(terrain_file), re.IGNORECASE)
            if tile_match:
                x = int(tile_match.group('tile_x'))
                y = int(tile_match.group('tile_y'))
                if tile_flip_x:
                    pos_x = float(tile_width * -x) + (float(terrain_width) / 2) - float(tile_width / 2)
                else:
                    pos_x = float(tile_width * x) - (float(terrain_width) / 2) + float(tile_width / 2)

                if tile_flip_y:
                    pos_y = float(tile_length * y) - (float(terrain_length) / 2) + float(tile_length / 2)
                else:
                    pos_y = float(tile_length * -y) + (float(terrain_length) / 2) - float(tile_length / 2)

                position = (pos_x, 0, pos_y)
                terrain_tile = create_terrain(terrain_file, terrain_name='{}_x{}_y{}'.format(terrain_name, x, y),
                                              ctx=terrain_ctx, dimensions=tile_dimensions,
                                              position=position, **kwargs)
                tiles.append(terrain_tile)
    else:
        tile_width = float(dimensions[0]) / divisions_x
        tile_length = float(dimensions[1]) / divisions_y
        tile_dimensions = (tile_width, tile_length, dimensions[2])

        for y in range(0, divisions_y):
            for x in range(0, divisions_x):
                u_offset = ((divisions_x - 1) * 0.5) - x
                v_offset = ((divisions_y - 1) * 0.5) - y
                position = (float(tile_width * x) - (float(terrain_width) / 2) + float(tile_width / 2), 0,
                            float(tile_length * -y) + (float(terrain_length) / 2) - float(tile_length / 2))
                # num_tiles = tile offset
                # 2 = -0.5, 0.5
                # 3 = -1, 0, 1
                # 4 = -1.5, -0.5, 0.5, 1.5
                # 5 = -2, -1, 0, 1, 2
                # 6 = -2.5, -1.5, -0.5, 0.5, 1.5, 2.5
                terrain_tile = create_terrain(heightmap_file, terrain_name='{}_x{}_y{}'.format(terrain_name, x, y),
                                              u_offset=u_offset, v_offset=v_offset, u_scale=divisions_x,
                                              v_scale=divisions_y, ctx=terrain_ctx, dimensions=tile_dimensions,
                                              position=position, **kwargs)
                tiles.append(terrain_tile)

    terrain_root_ctrl = ix.cmds.CombineItems(tiles, str(terrain_ctx))
    ix.cmds.RenameItem(str(terrain_root_ctrl), 'terrain_master_ctrl')
    ix.cmds.SetValue(str(terrain_root_ctrl) + ".display_pickable", ['0'])
    ix.cmds.SetValue(str(terrain_root_ctrl) + ".highlight_mode", ['1'])
    # Proxy switch boolean
    # ix.cmds.CreateCustomAttribute([str(terrain_root_ctrl)], "show_tiles", 0,
    #                               ["container", "vhint", "group", "count", "allow_expression"],
    #                               ["CONTAINER_SINGLE", "VISUAL_HINT_DEFAULT", "Terrain", "1", "0"])
    # ix.cmds.CreateCustomAttribute([str(terrain_root_ctrl)], "lod_center_object", 3,
    #                               ["container", "vhint", "group", "count", "allow_expression"],
    #                               ["CONTAINER_SINGLE", "VISUAL_HINT_DEFAULT", "Terrain", "1", "0"])
    # ix.cmds.CreateCustomAttribute([str(terrain_root_ctrl)], "lod_radius", 2,
    #                               ["container", "vhint", "group", "count", "allow_expression"],
    #                               ["CONTAINER_SINGLE", "VISUAL_HINT_DEFAULT", "Terrain", "1", "0"])
    #
    # ix.cmds.SetValue(str(terrain_root_ctrl) + ".lod_radius", ['1024'])

    # terrain_root_ctrl = ix.cmds.CreateObject("terrain_master_ctrl", "Locator", "Global", str(terrain_ctx))
    ix.application.check_for_events()
    for tile in tiles:
        ix.cmds.SetValue(str(tile) + ".unseen_by_renderer", ['1'])
        ix.cmds.LockAttributes([str(tile) + ".translate"], True)
        ix.cmds.LockAttributes([str(tile) + ".rotate"], True)
        ix.cmds.LockAttributes([str(tile) + ".scale"], True)
        # TODO: string expressions are broken in 4.0 SP1. Wait for fix in version > SP2
        # distance_expr = "output_var = 0.0;\n"
        # distance_expr += "lod_object = get_string(get_context(get_context()) + '/terrain_master_ctrl.lod_center_object');\n"
        # distance_expr += "testvar = log_info(lod_object);\n"
        # distance_expr += "if (lod_object != ''){\n"
        # distance_expr += "p1 = get_vec3(lod_object + '.translate');\n"
        # distance_expr += "p2 = get_vec3('translate');\n"
        # distance_expr += "lod_radius = get_double(get_context(get_context()) + '/terrain_master_ctrl.lod_radius');\n"
        # distance_expr += "testvar1 = log_info(lod_radius);\n"
        # distance_expr += "obj_distance = dist(p1[0], p1[1], p1[2], p2[0], p2[1], p2[2]);\n"
        # distance_expr += "testvar2 = log_info(obj_distance);\n"
        # distance_expr += "if (obj_distance > lod_radius){\noutput_var = 1.0;\n}\n"
        # distance_expr += "}\n"
        # distance_expr += "output_var"
        # print distance_expr
        # ix.cmds.SetExpression([str(tile) + ".proxy_control_by_lod"], [distance_expr])

        # show_tiles_expr = "out = 0;\n"
        #
        # ix.cmds.SetExpression([str(tile) + ".unseen_by_renderer"], [show_tiles_expr])
    return terrain_root_ctrl


def create_terrain(heightmap_file, terrain_name='terrain', ctx=None,
                   dimensions=('2048', '2048', '400'),
                   stream=True,
                   animated=False,
                   adaptive_spans=2048,
                   spans=1024,
                   proxy_adaptive_spans=1024,
                   proxy_spans=256,
                   generate_proxy=True,
                   repeat='edge',
                   displacement_mode=0,
                   use_midpoint=True,
                   position=(0, 0, 0),
                   u_offset=0.0, v_offset=0.0, u_scale=1.0, v_scale=1.0,
                   **kwargs):
    """Generates a displaced terrain from the selected heightmap. Dimensions are stored as [w,l,h]."""
    logging.debug("Generating terrain...")
    ix = get_ix(kwargs.get("ix"))
    if not ctx:
        ctx = ix.application.get_working_context()
    if not check_context(ctx, ix=ix):
        return None

    if not os.path.isfile(heightmap_file):
        ix.log_warning('Invalid heightmap file specified.')
        return None

    terrain_geo_items = []

    terrain_ctx = ix.cmds.CreateContext(terrain_name, "Global", str(ctx))

    spans_x = spans
    spans_y = spans
    proxy_spans_x = proxy_spans
    proxy_spans_y = proxy_spans
    # Check if resolution is non-uniform and rescale spans to maintain quads.
    if not dimensions[0] == dimensions[1]:
        if dimensions[0] > dimensions[1]:
            spans_y = int(float(dimensions[1]) / (dimensions[0]) * spans)
            proxy_spans_y = int(float(dimensions[1]) / (dimensions[0]) * proxy_spans)
        if dimensions[0] < dimensions[1]:
            spans_x = int(float(dimensions[0]) / (dimensions[1]) * spans)
            proxy_spans_x = int(float(dimensions[0]) / (dimensions[1]) * proxy_spans)

    terrain_geo = ix.cmds.CreateObject("terrain_geo", "GeometryPolygrid", "Global", str(terrain_ctx))
    ix.cmds.SetValue(str(terrain_geo) + ".displacement_adaptive_span_count", [str(adaptive_spans)])
    ix.cmds.SetValue(str(terrain_geo) + ".size[0]", [str(dimensions[0])])
    ix.cmds.SetValue(str(terrain_geo) + ".size[1]", [str(dimensions[1])])
    ix.cmds.SetValue(str(terrain_geo) + ".spans[0]", [str(spans_x)])
    ix.cmds.SetValue(str(terrain_geo) + ".spans[1]", [str(spans_y)])
    ix.cmds.SetValue(str(terrain_geo) + ".unseen_by_renderer", [str(1)])
    ix.cmds.SetValue(str(terrain_geo) + ".display_visible", [str(0)])
    terrain_geo_items.append(terrain_geo)

    if generate_proxy:
        proxy_geo = ix.cmds.Instantiate([str(terrain_geo)])[0]
        ix.cmds.LocalizeAttributes([str(proxy_geo) + ".displacement_adaptive_span_count", str(proxy_geo) + ".spans"],
                                   True)
        ix.cmds.SetValue(str(proxy_geo) + ".displacement_adaptive_span_count", [str(int(proxy_adaptive_spans))])
        ix.cmds.SetValue(str(proxy_geo) + ".spans[0]", [str(proxy_spans_x)])
        ix.cmds.SetValue(str(proxy_geo) + ".spans[1]", [str(proxy_spans_y)])
        ix.application.check_for_events()
        ix.cmds.RenameItem(str(proxy_geo), 'proxy_geo')
        ix.application.check_for_events()
        terrain_geo_items.append(proxy_geo)
    else:
        proxy_geo = None
    reorder_tx = None

    if stream:
        tx = ix.cmds.CreateObject('heightmap', "TextureStreamedMapFile", "Global", str(terrain_ctx))
        if displacement_mode == 0:
            reorder_tx = ix.cmds.CreateObject('heightmap' + SINGLE_CHANNEL_SUFFIX, "TextureReorder",
                                              "Global", str(terrain_ctx))
            ix.cmds.SetValue(str(reorder_tx) + ".channel_order[0]", ["rrrr"])
            ix.cmds.SetTexture([str(reorder_tx) + ".input"], str(tx))
        attrs = ix.api.CoreStringArray(6)
        attrs[0] = str(tx) + ".interpolation_mode"
        attrs[1] = str(tx) + ".mipmap_mode"
        attrs[2] = str(tx) + ".u_repeat_mode"
        attrs[3] = str(tx) + ".v_repeat_mode"
        attrs[4] = str(tx) + ".use_raw_data"
        attrs[5] = str(tx) + ".filename"
        values = ix.api.CoreStringArray(6)
        values[0] = str(3)
        values[1] = str(3)
        values[2] = str(2 if repeat == 'edge' else 3)
        values[3] = str(2 if repeat == 'edge' else 3)
        values[4] = str(1)
        values[5] = r'{}'.format(heightmap_file)
        ix.cmds.SetValues(attrs, values)
    else:
        tx = ix.cmds.CreateObject('heightmap', "TextureMapFile", "Global", str(terrain_ctx))
        attrs = ix.api.CoreStringArray(5)
        attrs[0] = str(tx) + ".single_channel_file_behavior"
        attrs[1] = str(tx) + ".u_repeat_mode"
        attrs[2] = str(tx) + ".v_repeat_mode"
        attrs[3] = str(tx) + ".use_raw_data"
        attrs[4] = str(tx) + ".filename"
        values = ix.api.CoreStringArray(5)
        values[0] = str(1)
        values[1] = str(1 if repeat == 'edge' else 0)
        values[2] = str(1 if repeat == 'edge' else 0)
        values[3] = str(1)
        values[4] = r'{}'.format(heightmap_file)
        ix.cmds.SetValues(attrs, values)

    # set projection scale
    if 1 not in [u_scale, v_scale]:
        attrs = ix.api.CoreStringArray(4)
        attrs[0] = str(tx) + ".uv_translate[0]"
        attrs[1] = str(tx) + ".uv_translate[1]"
        attrs[2] = str(tx) + ".uv_scale[0]"
        attrs[3] = str(tx) + ".uv_scale[1]"
        values = ix.api.CoreStringArray(4)
        values[0] = str(u_offset)
        values[1] = str(v_offset)
        values[2] = str(u_scale)
        values[3] = str(v_scale)
        ix.cmds.SetValues(attrs, values)

    if animated:
        ix.cmds.SetValue(str(tx) + ".sequence_mode", [str(1)])
        tx.call_action("detect_sequence")
        ix.application.check_for_events()
        ix.cmds.SetValue(str(tx) + ".pre_behavior", [str(2)])
        ix.cmds.SetValue(str(tx) + ".post_behavior", [str(2)])

    disp = ix.cmds.CreateObject(terrain_name + DISPLACEMENT_MAP_SUFFIX, "Displacement",
                                "Global", str(terrain_ctx))
    attrs = ix.api.CoreStringArray(6)
    attrs[0] = str(disp) + ".bound[0]"
    attrs[1] = str(disp) + ".bound[1]"
    attrs[2] = str(disp) + ".bound[2]"
    attrs[3] = str(disp) + ".front_value"
    attrs[4] = str(disp) + ".front_offset"
    attrs[5] = str(disp) + ".front_direction"
    values = ix.api.CoreStringArray(6)
    values[0] = str(dimensions[2] * 1.1)
    values[1] = str(dimensions[2] * 1.1)
    values[2] = str(dimensions[2] * 1.1)
    values[3] = str(dimensions[2])
    values[4] = str(-0.5 if use_midpoint else 0)
    values[5] = str(displacement_mode)
    ix.cmds.SetValues(attrs, values)
    ix.application.check_for_events()
    ix.cmds.SetTexture([str(disp) + ".front_value"], str(reorder_tx if reorder_tx else tx))

    if generate_proxy:
        switcher_grp = ix.cmds.CreateObject(terrain_name + GROUP_SUFFIX, "Group", "Global", str(terrain_ctx))
        terrain_ctrl = ix.cmds.CombineItems([str(switcher_grp)], str(terrain_ctx))
        ix.cmds.RenameItem(str(terrain_ctrl), 'terrain_ctrl')
        attrs = ix.api.CoreStringArray(3)
        attrs[0] = str(terrain_ctrl) + ".translate_offset[0]"
        attrs[1] = str(terrain_ctrl) + ".translate_offset[1]"
        attrs[2] = str(terrain_ctrl) + ".translate_offset[2]"
        values = ix.api.CoreStringArray(3)
        values[0] = str(position[0])
        values[1] = str(position[1])
        values[2] = str(position[2])
        ix.cmds.SetValues(attrs, values)

        # Proxy switch boolean
        ix.cmds.CreateCustomAttribute([str(terrain_ctrl)], "proxy", 0,
                                      ["container", "vhint", "group", "count", "allow_expression"],
                                      ["CONTAINER_SINGLE", "VISUAL_HINT_DEFAULT", "Terrain", "1", "0"])
        # ix.cmds.CreateCustomAttribute([str(terrain_ctrl)], "proxy_control_by_lod", 0,
        #                               ["container", "vhint", "group", "count", "allow_expression"],
        #                               ["CONTAINER_SINGLE", "VISUAL_HINT_DEFAULT", "Terrain", "1", "0"])
        # Heightmap filename
        ix.cmds.CreateCustomAttribute([str(terrain_ctrl)], "filename", 4,
                                      ["container", "vhint", "group", "count", "allow_expression"],
                                      ["CONTAINER_SINGLE", "VISUAL_HINT_DEFAULT", "Terrain", "1", "0"])
        # Width
        ix.cmds.CreateCustomAttribute([str(terrain_ctrl)], "terrain_width", 2,
                                      ["container", "vhint", "group", "count", "allow_expression"],
                                      ["CONTAINER_SINGLE", "VISUAL_HINT_DEFAULT", "Terrain", "1", "0"])
        # Length
        ix.cmds.CreateCustomAttribute([str(terrain_ctrl)], "terrain_length", 2,
                                      ["container", "vhint", "group", "count", "allow_expression"],
                                      ["CONTAINER_SINGLE", "VISUAL_HINT_DEFAULT", "Terrain", "1", "0"])
        # Height
        ix.cmds.CreateCustomAttribute([str(terrain_ctrl)], "terrain_height", 2,
                                      ["container", "vhint", "group", "count", "allow_expression"],
                                      ["CONTAINER_SINGLE", "VISUAL_HINT_DEFAULT", "Terrain", "1", "0"])
        # Displacement spans
        ix.cmds.CreateCustomAttribute([str(terrain_ctrl)], "adaptive_spans", 1,
                                      ["container", "vhint", "group", "count", "allow_expression"],
                                      ["CONTAINER_SINGLE", "VISUAL_HINT_DEFAULT", "Terrain", "1", "0"])
        # Polygrid spans
        ix.cmds.CreateCustomAttribute([str(terrain_ctrl)], "spans_x", 1,
                                      ["container", "vhint", "group", "count", "allow_expression"],
                                      ["CONTAINER_SINGLE", "VISUAL_HINT_DEFAULT", "Terrain", "1", "0"])
        ix.cmds.CreateCustomAttribute([str(terrain_ctrl)], "spans_y", 1,
                                      ["container", "vhint", "group", "count", "allow_expression"],
                                      ["CONTAINER_SINGLE", "VISUAL_HINT_DEFAULT", "Terrain", "1", "0"])
        # Proxy adaptive spans
        ix.cmds.CreateCustomAttribute([str(terrain_ctrl)], "proxy_adaptive_spans", 1,
                                      ["container", "vhint", "group", "count", "allow_expression"],
                                      ["CONTAINER_SINGLE", "VISUAL_HINT_DEFAULT", "Terrain", "1", "0"])
        # Proxy spans
        ix.cmds.CreateCustomAttribute([str(terrain_ctrl)], "proxy_spans_x", 1,
                                      ["container", "vhint", "group", "count", "allow_expression"],
                                      ["CONTAINER_SINGLE", "VISUAL_HINT_DEFAULT", "Terrain", "1", "0"])
        ix.cmds.CreateCustomAttribute([str(terrain_ctrl)], "proxy_spans_y", 1,
                                      ["container", "vhint", "group", "count", "allow_expression"],
                                      ["CONTAINER_SINGLE", "VISUAL_HINT_DEFAULT", "Terrain", "1", "0"])

        ix.cmds.SetValue(str(terrain_ctrl) + ".proxy", [str(1)])
        # ix.cmds.SetValue(str(terrain_ctrl) + ".proxy_control_by_lod", [str(0)])
        ix.cmds.SetValue(str(terrain_ctrl) + ".filename", [heightmap_file])
        ix.cmds.SetValue(str(terrain_ctrl) + ".terrain_width", [str(dimensions[0])])
        ix.cmds.SetValue(str(terrain_ctrl) + ".terrain_length", [str(dimensions[1])])
        ix.cmds.SetValue(str(terrain_ctrl) + ".terrain_height", [str(dimensions[2])])
        ix.cmds.SetValue(str(terrain_ctrl) + ".adaptive_spans", [str(adaptive_spans)])
        ix.cmds.SetValue(str(terrain_ctrl) + ".spans_x", [str(spans_x)])
        ix.cmds.SetValue(str(terrain_ctrl) + ".spans_y", [str(spans_y)])
        ix.cmds.SetValue(str(terrain_ctrl) + ".proxy_adaptive_spans", [str(int(proxy_adaptive_spans))])
        ix.cmds.SetValue(str(terrain_ctrl) + ".proxy_spans_x", [str(int(proxy_spans_x))])
        ix.cmds.SetValue(str(terrain_ctrl) + ".proxy_spans_y", [str(int(proxy_spans_y))])

        ix.application.check_for_events()
        ix.cmds.SetExpression([str(switcher_grp) + ".inclusion_rule[0]"],
                              ["get_double('terrain_ctrl.proxy') == 0 ? './terrain_geo' : './proxy_geo'"])
        ix.cmds.SetExpression([str(terrain_geo) + ".size[0]"],
                              ["get_double('terrain_ctrl.terrain_width')"])
        ix.cmds.SetExpression([str(terrain_geo) + ".size[1]"],
                              ["get_double('terrain_ctrl.terrain_length')"])
        ix.cmds.SetExpression([str(disp) + ".front_value"],
                              ["get_double('terrain_ctrl.terrain_height')"])
        ix.cmds.SetExpression([str(tx) + ".filename"],
                              ["get_string('terrain_ctrl.filename')"])
        ix.cmds.SetExpression([str(terrain_geo) + ".displacement_adaptive_span_count"],
                              ["get_double('terrain_ctrl.adaptive_spans')"])
        ix.cmds.SetExpression([str(terrain_geo) + ".spans[0]"],
                              ["get_double('terrain_ctrl.spans_x')"])
        ix.cmds.SetExpression([str(terrain_geo) + ".spans[1]"],
                              ["get_double('terrain_ctrl.spans_y')"])
        ix.cmds.SetExpression([str(proxy_geo) + ".displacement_adaptive_span_count"],
                              ["get_double('terrain_ctrl.proxy_adaptive_spans')"])
        ix.cmds.SetExpression([str(proxy_geo) + ".spans[0]"],
                              ["get_double('terrain_ctrl.proxy_spans_x')"])
        ix.cmds.SetExpression([str(proxy_geo) + ".spans[1]"],
                              ["get_double('terrain_ctrl.proxy_spans_y')"])
    else:
        terrain_ctrl = terrain_geo

    for geometry in terrain_geo_items:
        geo = geometry.get_module()
        for i in range(geo.get_shading_group_count()):
            geo.assign_displacement(disp.get_module(), i)

    return terrain_ctrl
