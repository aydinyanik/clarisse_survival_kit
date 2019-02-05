from clarisse_survival_kit.selectors import *
from clarisse_survival_kit.utility import *
from clarisse_survival_kit.surface import Surface
import importlib


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

    connected_attrs = ix.api.OfAttrVector()
    get_attrs_connected_to_texture(diffuse_tx, connected_attrs, ix=ix)
    for i_attr in range(0, connected_attrs.get_count()):
        logging.debug("Replace attr: " + str(connected_attrs[i_attr]))
        ix.cmds.SetTexture([str(connected_attrs[i_attr])], str(diffuse_blend_tx))
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

    connected_attrs = ix.api.OfAttrVector()
    get_attrs_connected_to_texture(specular_tx, connected_attrs, ix=ix)
    for i_attr in range(0, connected_attrs.get_count()):
        logging.debug("Replace attr: " + str(connected_attrs[i_attr]))
        ix.cmds.SetTexture([str(connected_attrs[i_attr])], str(specular_blend_tx))
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

    connected_attrs = ix.api.OfAttrVector()
    get_attrs_connected_to_texture(roughness_tx, connected_attrs, ix=ix)
    for i_attr in range(0, connected_attrs.get_count()):
        logging.debug("Replace attr: " + str(connected_attrs[i_attr]))
        ix.cmds.SetTexture([str(connected_attrs[i_attr])], str(roughness_blend_tx))
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
            if report.get('surface_height'):
                surface_height = report.get('surface_height')
            if report.get('tileable'):
                tileable = report.get('tileable')
            break
        else:
            logging.debug('Provider %s did not pass inspection' % provider_name)
            if selected_provider:
                ix.log_warning('Content provider could not find asset in the specified directory.')
                return None


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
    surface.update_displacement(surface_height)
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
            print "Base surface height: " + str(base_srf_height)
            base_disp_tx_front_value = ix.get_item(str(base_disp) + ".front_value")
            base_disp_tx = base_disp_tx_front_value.get_texture()
            base_disp_height_scale_tx = ix.cmds.CreateObject(mix_srf_name + DISPLACEMENT_HEIGHT_SCALE_SUFFIX,
                                                             "TextureMultiply", "Global", str(mix_selectors_ctx))
            ix.cmds.SetTexture([str(base_disp_height_scale_tx) + ".input1"], str(base_disp_tx))

            base_disp_height_scale_tx.attrs.input2[0] = base_srf_height
            base_disp_height_scale_tx.attrs.input2[1] = base_srf_height
            base_disp_height_scale_tx.attrs.input2[2] = base_srf_height
            base_disp_blend_offset_tx = ix.cmds.CreateObject(mix_srf_name + DISPLACEMENT_BLEND_OFFSET_SUFFIX,
                                                             "TextureAdd", "Global", str(mix_selectors_ctx))
            ix.cmds.SetTexture([str(base_disp_blend_offset_tx) + ".input1"], str(base_disp_height_scale_tx))
            base_disp_offset_tx = ix.cmds.CreateObject(mix_srf_name + DISPLACEMENT_OFFSET_SUFFIX, "TextureAdd",
                                                       "Global", str(mix_selectors_ctx))
            base_disp_offset_tx.attrs.input2[0] = -0.5 * base_srf_height + 0.5
            base_disp_offset_tx.attrs.input2[1] = -0.5 * base_srf_height + 0.5
            base_disp_offset_tx.attrs.input2[2] = -0.5 * base_srf_height + 0.5
            ix.cmds.SetTexture([str(base_disp_offset_tx) + ".input1"], str(base_disp_height_scale_tx))

            # Surface 2
            print "Setting up surface 2"
            cover_srf_height = cover_disp.attrs.front_value[0]
            print "Surface 2 height: " + str(cover_srf_height)
            cover_disp_tx_front_value = ix.get_item(str(cover_disp) + ".front_value")
            cover_disp_tx = cover_disp_tx_front_value.get_texture()
            cover_disp_height_scale_tx = ix.cmds.CreateObject(cover_name + DISPLACEMENT_HEIGHT_SCALE_SUFFIX,
                                                              "TextureMultiply", "Global", str(mix_selectors_ctx))
            ix.cmds.SetTexture([str(cover_disp_height_scale_tx) + ".input1"], str(cover_disp_tx))
            cover_disp_height_scale_tx.attrs.input2[0] = cover_srf_height
            cover_disp_height_scale_tx.attrs.input2[1] = cover_srf_height
            cover_disp_height_scale_tx.attrs.input2[2] = cover_srf_height
            cover_disp_blend_offset_tx = ix.cmds.CreateObject(cover_name + DISPLACEMENT_BLEND_OFFSET_SUFFIX,
                                                              "TextureAdd", "Global", str(mix_selectors_ctx))
            ix.cmds.SetTexture([str(cover_disp_blend_offset_tx) + ".input1"], str(cover_disp_height_scale_tx))
            cover_disp_offset_tx = ix.cmds.CreateObject(cover_name + DISPLACEMENT_OFFSET_SUFFIX, "TextureAdd",
                                                        "Global", str(mix_selectors_ctx))
            cover_disp_offset_tx.attrs.input2[0] = -0.5 * cover_srf_height + 0.5
            cover_disp_offset_tx.attrs.input2[1] = -0.5 * cover_srf_height + 0.5
            cover_disp_offset_tx.attrs.input2[2] = -0.5 * cover_srf_height + 0.5
            ix.cmds.SetTexture([str(cover_disp_offset_tx) + ".input1"], str(cover_disp_height_scale_tx))

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
        ix.cmds.SetTexture([new_preview_mtl.get_full_name() + ".front_color"],
                           str(diffuse_tx))
        connected_attrs = ix.api.OfAttrVector()
        get_attrs_connected_to_texture(mtl, connected_attrs, ix=ix)
        for i in range(0, connected_attrs.get_count()):
            ix.cmds.SetValues([connected_attrs[i].get_full_name()], [str(new_preview_mtl)])
        ix.selection.select(mtl)
        ix.application.select_next_outputs()
        for sel in ix.selection:
            if sel.is_kindof("Geometry"):
                shading_group = sel.get_module().get_geometry().get_shading_group_names()
                count = shading_group.get_count()
                for j in range(count):
                    shaders = sel.attrs.materials[j]
                    if shaders == mtl:
                        ix.cmds.SetValues([sel.get_full_name() + ".materials" + str([j])], [str(new_preview_mtl)])
    else:
        logging.debug("Reverting back to complex mode...")
        connected_attrs = ix.api.OfAttrVector()
        get_attrs_connected_to_texture(preview_mtl, connected_attrs, ix=ix)
        for i in range(0, connected_attrs.get_count()):
            ix.cmds.SetValues([connected_attrs[i].get_full_name()], [mtl.get_full_name()])
        ix.selection.select(preview_mtl)
        ix.application.select_next_outputs()
        for sel in ix.selection:
            if sel.is_kindof("Geometry"):
                shading_group = sel.get_module().get_geometry().get_shading_group_names()
                count = shading_group.get_count()
                for j in range(count):
                    shaders = sel.attrs.materials[j]
                    if shaders == preview_mtl:
                        ix.cmds.SetValues([sel.get_full_name() + ".materials" + str([j])], [str(mtl)])
        ix.cmds.DeleteItems([preview_mtl.get_full_name()])
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


