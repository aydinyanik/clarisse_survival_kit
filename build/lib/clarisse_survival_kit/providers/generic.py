from clarisse_survival_kit.settings import *
from clarisse_survival_kit.utility import *
from clarisse_survival_kit.surface import Surface


def inspect_asset(asset_directory):
    report = {}
    if get_textures_from_directory(asset_directory):
        report['has_textures'] = True
        if get_geometry_from_directory(asset_directory):
            report['has_geometry'] = True
    return report


def import_asset(asset_directory, report, **kwargs):
    surface = None
    if report.get('has_textures'):
        logging.debug('Importing surface with arguments: ' + str(kwargs))
        surface = import_surface(asset_directory, **kwargs)
    if report.get('has_geometry'):
        target_ctx = None
        if surface:
            target_ctx = surface.ctx
        geometry = import_geometry(asset_directory, target_ctx=target_ctx, surface=surface, **kwargs)


def import_surface(asset_directory, target_ctx=None, ior=DEFAULT_IOR, metallic_ior=DEFAULT_METALLIC_IOR,
                   projection_type="triplanar", object_space=0, clip_opacity=True,
                   color_spaces=(), triplanar_blend=0.5, **kwargs):
    # Initial data
    ix = get_ix(kwargs.get("ix"))
    if not target_ctx:
        target_ctx = ix.application.get_working_context()
    if not check_context(target_ctx, ix=ix):
        return None
    asset_directory = os.path.normpath(asset_directory)
    if not os.path.isdir(asset_directory):
        ix.log_warning("Invalid directory specified: " + asset_directory)
        return None
    logging.debug("Asset directory: " + asset_directory)

    logging.debug("Importing generic surface:")
    surface_height = DEFAULT_DISPLACEMENT_HEIGHT
    scan_area = DEFAULT_UV_SCALE
    tileable = True
    asset_name = os.path.basename(os.path.normpath(asset_directory))

    textures = get_textures_from_directory(asset_directory)
    if not textures:
        ix.log_warning("No textures found in directory.")
        return None
    logging.debug("Found textures: ")
    logging.debug(str(textures))
    streamed_maps = get_stream_map_files(textures)
    if streamed_maps:
        logging.debug("Streamed maps: ")
        logging.debug(str(streamed_maps))

    surface = Surface(ix, projection=projection_type, uv_scale=scan_area, height=surface_height, tile=tileable,
                      object_space=object_space, triplanar_blend=triplanar_blend, ior=ior, metallic_ior=metallic_ior)
    mtl = surface.create_mtl(asset_name, target_ctx)
    surface.create_textures(textures, color_spaces, streamed_maps, clip_opacity=clip_opacity)

    logging.debug("Finished importing surface.")
    logging.debug("+++++++++++++++++++++++++++++++")
    return surface


def import_geometry(asset_directory, target_ctx=None, surface=None, clip_opacity=True, obj_scale=0.01, **kwargs):
    ix = get_ix(kwargs.get("ix"))
    if not target_ctx:
        target_ctx = ix.application.get_working_context()
    if not check_context(target_ctx, ix=ix):
        return None
    asset_directory = os.path.normpath(asset_directory)
    if not os.path.isdir(asset_directory):
        ix.log_warning("Invalid directory specified: " + asset_directory)
        return None
    logging.debug("Geo directory: " + asset_directory)

    logging.debug("Importing geometry:")
    asset_name = os.path.basename(os.path.normpath(asset_directory))

    geometry = get_geometry_from_directory(asset_directory)
    if not geometry:
        ix.log_warning("No geometry found in directory.")
        return None
    logging.debug("Found geometry: ")
    logging.debug(str(geometry))

    geo_items = []

    for geo_file in geometry:
        filename, extension = os.path.splitext(geo_file)
        if extension in [".obj", ".lwo"]:
            polyfile = ix.cmds.CreateObject(os.path.splitext(os.path.basename(geo_file))[0],
                                            "GeometryPolyfile", "Global", str(target_ctx))
            ix.cmds.SetValue(str(polyfile) + ".filename", [os.path.normpath(os.path.join(asset_directory, geo_file))])
            # Megascans .obj files are saved in cm, Clarisse imports them as meters.
            polyfile.attrs.scale_offset[0] = obj_scale
            polyfile.attrs.scale_offset[1] = obj_scale
            polyfile.attrs.scale_offset[2] = obj_scale
            geo_items.append(polyfile)
            if surface:
                geo = polyfile.get_module()
                for i in range(geo.get_shading_group_count()):
                    geo.assign_material(surface.mtl.get_module(), i)
                    if clip_opacity and surface.get('opacity'):
                        geo.assign_clip_map(surface.get('opacity').get_module(), i)
                    if surface.get('displacement') and surface.get('displacement_map'):
                        geo.assign_displacement(surface.get('displacement_map').get_module(), i)
        elif extension == ".abc":
            abc_reference = ix.cmds.CreateFileReference(str(target_ctx),
                                                        [os.path.normpath(os.path.join(asset_directory, geo_file))])
            geo_items.append(abc_reference)
    if geo_items:
        logging.debug("Creating geometry group..")
        group = ix.cmds.CreateObject(asset_name + GROUP_SUFFIX, "Group", "Global", str(target_ctx))
        group.attrs.inclusion_rule = "./*"
        ix.cmds.AddValues([group.get_full_name() + ".filter"], ["GeometryAbcMesh"])
        ix.cmds.AddValues([group.get_full_name() + ".filter"], ["GeometryPolyfile"])
        ix.cmds.RemoveValue([group.get_full_name() + ".filter"], [2, 0, 1])
        logging.debug("...done creating geometry group")
        if surface:
            logging.debug("Creating shading layers..")
            shading_layer = ix.cmds.CreateObject(asset_name + SHADING_LAYER_SUFFIX, "ShadingLayer", "Global",
                                                 str(target_ctx))
            ix.cmds.AddShadingLayerRule(str(shading_layer), 0, ["filter", "", "is_visible", "1"])
            ix.cmds.SetShadingLayerRulesProperty(str(shading_layer), [0], "filter", ["./*"])
            ix.cmds.SetShadingLayerRulesProperty(str(shading_layer), [0], "material", [str(surface.mtl)])
            if surface.get('opacity') and clip_opacity:
                ix.cmds.SetShadingLayerRulesProperty(str(shading_layer), [0], "clip_map",
                                                     [str(surface.get('opacity'))])
            if surface.get('displacement'):
                ix.cmds.SetShadingLayerRulesProperty(str(shading_layer), [0], "displacement",
                                                     [str(surface.get('displacement_map'))])
            logging.debug("...done creating shading layers")

    logging.debug("Finished importing geometry.")
    logging.debug("+++++++++++++++++++++++++++++++")
    return geo_items

