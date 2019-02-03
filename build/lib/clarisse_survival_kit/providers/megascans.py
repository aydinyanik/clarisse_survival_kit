import json
import logging
import os
import multiprocessing.dummy as mp

from clarisse_survival_kit.settings import *
from clarisse_survival_kit.utility import *
from clarisse_survival_kit.surface import Surface


def inspect_asset(asset_directory):
    json_data = get_json_data_from_directory(asset_directory)
    if json_data:
        return json_data
    else:
        return None


def import_asset(asset_directory, report=None, **kwargs):
    ix = get_ix(kwargs.get('ix'))
    asset_directory = os.path.join(os.path.normpath(asset_directory), '')
    if not report:
        report = inspect_asset(asset_directory)
    if report:
        if not kwargs.get('color_spaces'):
            kwargs['color_spaces'] = get_color_spaces(MEGASCANS_COLOR_SPACES, ix=ix)
        asset_type = report.get('type')
        if asset_type:
            if asset_type == 'surface':
                import_surface(asset_directory, **kwargs)
            elif asset_type == '3d':
                import_3d(asset_directory, **kwargs)
            elif asset_type == '3dplant':
                import_3dplant(asset_directory, **kwargs)
            elif asset_type == 'atlas':
                import_atlas(asset_directory, **kwargs)


def import_surface(asset_directory, target_ctx=None, ior=DEFAULT_IOR, projection_type='triplanar', object_space=0,
                   clip_opacity=True, color_spaces=None, triplanar_blend=0.5, **kwargs):
    """Imports a Megascans surface."""
    logging.debug("++++++++++++++++++++++.")
    logging.debug("Import Megascans surface called.")
    ix = get_ix(kwargs.get('ix'))
    if not target_ctx:
        target_ctx = ix.application.get_working_context()
    if not check_context(target_ctx, ix=ix):
        return None
    if not os.path.isdir(asset_directory):
        return ix.log_warning('Invalid directory specified: ' + asset_directory)
    if not color_spaces:
        color_spaces = get_color_spaces(MEGASCANS_COLOR_SPACES, ix=ix)
    logging.debug('Asset directory: ' + asset_directory)

    # Initial data
    json_data = get_json_data_from_directory(asset_directory)
    logging.debug('JSON data:')
    logging.debug(str(json_data))
    if not json_data:
        ix.log_warning('Could not find a Megascans JSON file. Defaulting to standard settings.')
    surface_height = json_data.get('surface_height', DEFAULT_DISPLACEMENT_HEIGHT)
    logging.debug('Surface height JSON test: ' + str(surface_height))
    scan_area = json_data.get('scan_area', DEFAULT_UV_SCALE)
    logging.debug('Scan area JSON test: ' + str(scan_area))
    tileable = json_data.get('tileable', True)
    asset_name = os.path.basename(os.path.normpath(asset_directory))
    logging.debug('Asset name: ' + asset_name)

    # All assets except 3dplant have the material in the root directory of the asset.
    logging.debug('Searching for textures: ')
    textures = get_textures_from_directory(asset_directory)
    if not textures:
        ix.log_warning('No textures found in directory.')
        return None
    logging.debug('Found textures: ')
    logging.debug(str(textures))
    streamed_maps = get_stream_map_files(textures)
    if streamed_maps:
        logging.debug('Streamed maps: ')
        logging.debug(str(streamed_maps))

    surface = Surface(ix, projection=projection_type, uv_scale=scan_area, height=surface_height, tile=tileable,
                      object_space=object_space, triplanar_blend=triplanar_blend, ior=ior)
    mtl = surface.create_mtl(asset_name, target_ctx)
    surface.create_textures(textures, color_spaces=color_spaces,
                            streamed_maps=streamed_maps, clip_opacity=clip_opacity)
    logging.debug("Import Megascans surface done.")
    logging.debug("++++++++++++++++++++++.")
    return surface


def import_3d(asset_directory, target_ctx=None, clip_opacity=True, **kwargs):
    """Imports a Megascans 3D object."""
    ix = get_ix(kwargs.get('ix'))
    logging.debug("*******************************")
    logging.debug("Importing Megascans 3d asset...")
    # Force projection to uv
    kwargs['projection_type'] = 'uv'
    surface = import_surface(asset_directory=asset_directory, target_ctx=target_ctx, clip_opacity=clip_opacity,
                             **kwargs)
    asset_name = surface.name
    mtl = surface.mtl
    ctx = surface.ctx
    textures = get_textures_from_directory(asset_directory)

    lod_mtls = {}
    if 'normal_lods' in textures and 'normal' in textures:
        logging.debug("Setting up normal lods: ")
        normal_lods = {}
        for normal_lod_file in textures['normal_lods']:
            logging.debug(str(normal_lod_file))
            lod_filename, lod_ext = os.path.splitext(normal_lod_file)
            lod_level_match = re.sub('.*?([0-9]*)$', r'\1', lod_filename)
            lod_level = int(lod_level_match)
            logging.debug("LOD level: " + str(lod_level))
            lod_mtl = ix.cmds.Instantiate([str(mtl)])[0]
            ix.cmds.LocalizeAttributes([str(lod_mtl) + ".normal_input"], True)
            ix.cmds.RenameItem(str(lod_mtl), asset_name + MATERIAL_LOD_SUFFIX % lod_level)
            normal_lod_tx = ix.cmds.Instantiate([str(surface.get('normal'))])[0]
            ix.cmds.LocalizeAttributes([str(normal_lod_tx) + ".filename"], True)
            ix.cmds.RenameItem(str(normal_lod_tx), asset_name + NORMAL_LOD_SUFFIX % lod_level)
            normal_lod_map = ix.cmds.CreateObject(asset_name + NORMAL_MAP_LOD_SUFFIX % lod_level,
                                                  "TextureNormalMap", "Global", str(ctx))
            ix.cmds.SetTexture([str(lod_mtl) + ".normal_input"], str(normal_lod_map))
            ix.cmds.SetTexture([str(normal_lod_map) + ".input"], str(normal_lod_tx))
            ix.cmds.SetValue(str(normal_lod_tx) + ".filename", [normal_lod_file])
            normal_lods[lod_level] = normal_lod_tx
            lod_mtls[lod_level_match] = lod_mtl
            lod_level += 1
    files = [f for f in os.listdir(asset_directory) if os.path.isfile(os.path.join(asset_directory, f))]
    for f in files:
        filename, extension = os.path.splitext(f)
        if extension == ".obj":
            logging.debug("Found normal lod obj: " + f)
            if "normal_lods" in textures and re.search(r'_LOD[0-9]$', filename, re.IGNORECASE):
                lod_level = re.sub('.*?([0-9]*)$', r'\1', filename)
                object_material = lod_mtls[lod_level]
            else:
                object_material = mtl
            polyfile = ix.cmds.CreateObject(filename, "GeometryPolyfile", "Global", str(ctx))
            ix.cmds.SetValue(str(polyfile) + ".filename", [os.path.normpath(os.path.join(asset_directory, f))])
            # Megascans .obj files are saved in cm, Clarisse imports them as meters.
            polyfile.attrs.scale_offset[0] = .01
            polyfile.attrs.scale_offset[1] = .01
            polyfile.attrs.scale_offset[2] = .01
            geo = polyfile.get_module()
            for i in range(geo.get_shading_group_count()):
                geo.assign_material(object_material.get_module(), i)
                if clip_opacity and textures.get('opacity'):
                    geo.assign_clip_map(surface.get('opacity').get_module(), i)
                if not filename.endswith("_High") and textures.get('displacement'):
                    geo.assign_displacement(surface.get('displacement_map').get_module(), i)
        elif extension == ".abc":
            abc_reference = ix.cmds.CreateFileReference(str(ctx),
                                                        [os.path.normpath(os.path.join(asset_directory, f))])
    logging.debug("Creating shading layers..")
    shading_layer = ix.cmds.CreateObject(asset_name + SHADING_LAYER_SUFFIX, "ShadingLayer", "Global",
                                         str(ctx))
    ix.cmds.AddShadingLayerRule(str(shading_layer), 0, ["filter", "", "is_visible", "1"])
    ix.cmds.SetShadingLayerRulesProperty(str(shading_layer), [0], "filter", ["./*_High"])
    ix.cmds.SetShadingLayerRulesProperty(str(shading_layer), [0], "material", [str(mtl)])
    if surface.get('opacity') and clip_opacity:
        ix.cmds.SetShadingLayerRulesProperty(str(shading_layer), [0], "clip_map",
                                             [str(surface.get('opacity'))])
    if lod_mtls:
        i = 0
        for lod_level, lod_mtl in lod_mtls.iteritems():
            ix.cmds.AddShadingLayerRule(str(shading_layer), i, ["filter", "", "is_visible", "1"])
            ix.cmds.SetShadingLayerRulesProperty(str(shading_layer), [i], "filter", ["./*LOD" + str(lod_level)])
            ix.cmds.SetShadingLayerRulesProperty(str(shading_layer), [i], "material", [str(lod_mtl)])
            if surface.get('opacity') and clip_opacity:
                ix.cmds.SetShadingLayerRulesProperty(str(shading_layer), [i], "clip_map",
                                                     [str(surface.get('opacity'))])
            if surface.get('displacement'):
                if i in MESH_LOD_DISPLACEMENT_LEVELS:
                    ix.cmds.SetShadingLayerRulesProperty(str(shading_layer), [i], "displacement",
                                                         [str(surface.get('displacement_map'))])
            i += 1
    logging.debug("...done creating shading layers and importing 3d object.")
    logging.debug("********************************************************")


def import_atlas(asset_directory, target_ctx=None, clip_opacity=True, use_displacement=False, **kwargs):
    """Imports a Megascans 3D object."""
    ix = get_ix(kwargs.get('ix'))
    logging.debug("*******************")
    logging.debug("Setting up atlas...")

    # Force projection to UV
    kwargs['projection_type'] = 'uv'
    surface = import_surface(asset_directory=asset_directory, target_ctx=target_ctx, clip_opacity=clip_opacity,
                             **kwargs)
    asset_name = surface.name
    mtl = surface.mtl
    ctx = surface.ctx
    textures = get_textures_from_directory(asset_directory)

    files = [f for f in os.listdir(asset_directory) if os.path.isfile(os.path.join(asset_directory, f))]
    polyfiles = []
    for key, f in enumerate(files):
        filename, extension = os.path.splitext(f)
        if extension == ".obj":
            logging.debug("Found obj: " + f)
            polyfile = ix.cmds.CreateObject(filename, "GeometryPolyfile", "Global",
                                            str(ctx))
            polyfile.attrs.filename = os.path.normpath(os.path.join(asset_directory, f))
            geo = polyfile.get_module()
            for i in range(geo.get_shading_group_count()):
                geo.assign_material(mtl.get_module(), i)
                if textures.get('opacity') and clip_opacity:
                    geo.assign_clip_map(surface.get('opacity').get_module(), i)
                if textures.get('displacement') and use_displacement:
                    geo.assign_displacement(surface.get('displacement').get_module(), i)
            polyfiles.append(polyfile)
        elif extension == ".abc":
            logging.debug("Found abc: " + f)
            abc_reference = ix.cmds.CreateFileReference(str(ctx),
                                                        [os.path.normpath(os.path.join(asset_directory, f))])
    logging.debug("Setting up shading layer: ")
    if files:
        shading_layer = ix.cmds.CreateObject("shading_layer", "ShadingLayer", "Global",
                                             str(ctx))
        ix.cmds.AddShadingLayerRule(str(shading_layer), 0, ["filter", "", "is_visible", "1"])
        ix.cmds.SetShadingLayerRulesProperty(str(shading_layer), [0], "filter", ["./*"])
        ix.cmds.SetShadingLayerRulesProperty(str(shading_layer), [0], "material", [str(mtl)])
        if textures.get('opacity'):
            ix.cmds.SetShadingLayerRulesProperty(str(shading_layer), [0], "clip_map",
                                                 [str(surface.get('opacity'))])
        if textures.get('displacement'):
            ix.cmds.SetShadingLayerRulesProperty(str(shading_layer), [0], "displacement",
                                                 [str(surface.get('displacement_map'))])
    logging.debug("...done setting up shading layer")
    logging.debug("Setting up group: ")
    group = ix.cmds.CreateObject(asset_name + GROUP_SUFFIX, "Group", "Global", str(ctx))
    group.attrs.inclusion_rule = "./*"
    ix.cmds.AddValues([group.get_full_name() + ".filter"], ["GeometryAbcMesh"])
    ix.cmds.AddValues([group.get_full_name() + ".filter"], ["GeometryPolyfile"])
    ix.cmds.RemoveValue([group.get_full_name() + ".filter"], [2, 0, 1])
    logging.debug("...done setting up group and atlas")
    logging.debug("**********************************")


def import_3dplant(asset_directory, target_ctx=None, ior=DEFAULT_IOR, object_space=0, clip_opacity=True,
                   use_displacement=False, color_spaces=MEGASCANS_COLOR_SPACES, triplanar_blend=0.5, **kwargs):
    """Imports a Megascans 3D object."""
    ix = get_ix(kwargs.get('ix'))
    logging.debug("*******************")
    logging.debug("Setting up 3d plant...")

    # Megascans 3dplant importer. The 3dplant importer requires 2 materials to be created.
    # Let's first find the textures of the Atlas and create the material.
    if not target_ctx:
        target_ctx = ix.application.get_working_context()
    if not check_context(target_ctx, ix=ix):
        return None
    asset_directory = os.path.normpath(asset_directory)
    if not os.path.isdir(asset_directory):
        return ix.log_warning("Invalid directory specified: " + asset_directory)
    logging.debug("Asset directory: " + asset_directory)

    # Initial data
    json_data = get_json_data_from_directory(asset_directory)
    logging.debug("JSON data:")
    logging.debug(str(json_data))
    if not json_data:
        ix.log_warning("Could not find a Megascans JSON file. Defaulting to standard settings.")
    asset_type = json_data.get('type', 'surface')
    logging.debug("Asset type from JSON test: " + asset_type)
    surface_height = json_data.get('surface_height', DEFAULT_DISPLACEMENT_HEIGHT)
    logging.debug("Surface height JSON test: " + str(surface_height))
    scan_area = json_data.get('scan_area', DEFAULT_UV_SCALE)
    logging.debug("Scan area JSON test: " + str(scan_area))
    tileable = json_data.get('tileable', True)
    asset_name = os.path.basename(os.path.normpath(asset_directory))
    logging.debug("Asset name: " + asset_name)
    logging.debug(os.path.join(asset_directory, 'Textures/Atlas/'))
    atlas_textures = get_textures_from_directory(os.path.join(asset_directory, 'Textures/Atlas/'))
    if not atlas_textures:
        ix.log_warning("No atlas textures found in directory. Files might have been exported flattened from Bridge.\n"
                       "Testing import as Atlas.")
        import_atlas(asset_directory, target_ctx=target_ctx, use_displacement=use_displacement,
                     clip_opacity=clip_opacity, **kwargs)
        return None
    logging.debug("Atlas textures: ")
    logging.debug(str(atlas_textures))
    streamed_maps = get_stream_map_files(atlas_textures)
    logging.debug("Atlas streamed maps: ")
    logging.debug(str(streamed_maps))

    atlas_surface = Surface(ix, projection='uv', uv_scale=scan_area, height=DEFAULT_PLANT_DISPLACEMENT_HEIGHT,
                            tile=tileable, object_space=object_space, triplanar_blend=triplanar_blend, ior=ior)
    plant_root_ctx = ix.cmds.CreateContext(asset_name, "Global", str(target_ctx))
    atlas_mtl = atlas_surface.create_mtl(ATLAS_CTX, plant_root_ctx)
    atlas_surface.create_textures(atlas_textures, color_spaces=color_spaces, streamed_maps=streamed_maps,
                                  clip_opacity=clip_opacity)
    atlas_ctx = atlas_surface.ctx
    # Find the textures of the Billboard and create the material.
    billboard_textures = get_textures_from_directory(os.path.join(asset_directory, 'Textures/Billboard/'))
    if not billboard_textures:
        ix.log_warning("No textures found in directory.")
        return None
    logging.debug("Billboard textures: ")
    logging.debug(str(billboard_textures))

    streamed_maps = get_stream_map_files(billboard_textures)
    logging.debug("Billboard streamed maps: ")
    logging.debug(str(streamed_maps))
    billboard_surface = Surface(ix, projection='uv', uv_scale=scan_area, height=surface_height,
                                tile=tileable, object_space=object_space, triplanar_blend=triplanar_blend, ior=ior)
    billboard_mtl = billboard_surface.create_mtl(BILLBOARD_CTX, plant_root_ctx)
    billboard_surface.create_textures(billboard_textures, color_spaces=color_spaces, streamed_maps=streamed_maps,
                                      clip_opacity=clip_opacity)
    billboard_ctx = billboard_surface.ctx

    for dir_name in os.listdir(asset_directory):
        variation_dir = os.path.join(asset_directory, dir_name)
        if os.path.isdir(variation_dir) and dir_name.startswith('Var'):
            logging.debug("Variation dir found: " + variation_dir)
            files = [f for f in os.listdir(variation_dir) if os.path.isfile(os.path.join(variation_dir, f))]
            # Search for models files and apply material
            objs = []
            for f in files:
                filename, extension = os.path.splitext(f)
                if extension == ".obj":
                    logging.debug("Found obj: " + f)
                    filename, extension = os.path.splitext(f)
                    polyfile = ix.cmds.CreateObject(filename, "GeometryPolyfile", "Global", str(plant_root_ctx))
                    ix.cmds.SetValue(str(polyfile) + ".filename",
                                     [os.path.normpath(os.path.join(variation_dir, f))])
                    # Megascans .obj files are saved in cm, Clarisse imports them as meters.
                    polyfile.attrs.scale_offset[0] = .01
                    polyfile.attrs.scale_offset[1] = .01
                    polyfile.attrs.scale_offset[2] = .01
                    geo = polyfile.get_module()
                    for i in range(geo.get_shading_group_count()):
                        if filename.endswith('3'):
                            geo.assign_material(billboard_mtl.get_module(), i)
                            if clip_opacity and billboard_surface.get('opacity'):
                                geo.assign_clip_map((billboard_surface.get('opacity')).get_module(), i)
                        else:
                            geo.assign_material(atlas_mtl.get_module(), i)
                            if clip_opacity and atlas_surface.get('opacity'):
                                geo.assign_clip_map(atlas_surface.get('opacity').get_module(), i)
                            lod_level_match = re.sub('.*?([0-9]*)$', r'\1', filename)
                            if int(lod_level_match) in ATLAS_LOD_DISPLACEMENT_LEVELS and use_displacement:
                                geo.assign_displacement(atlas_surface.get('displacement_map').get_module(), i)
                elif extension == ".abc":
                    logging.debug("Found abc: " + f)
                    abc_reference = ix.cmds.CreateFileReference(str(plant_root_ctx),
                                                                [os.path.normpath(os.path.join(variation_dir, f))])

    shading_layer = ix.cmds.CreateObject(asset_name + SHADING_LAYER_SUFFIX, "ShadingLayer", "Global",
                                         str(plant_root_ctx))
    logging.debug("Creating shading layers and groups...")
    for i in range(0, 4):
        ix.cmds.AddShadingLayerRule(str(shading_layer), i, ["filter", "", "is_visible", "1"])
        ix.cmds.SetShadingLayerRulesProperty(str(shading_layer), [i], "filter", ["./*LOD" + str(i) + "*"])
        ix.cmds.SetShadingLayerRulesProperty(str(shading_layer), [i], "material", [str(atlas_mtl)])
        if atlas_surface.get('opacity') and clip_opacity:
            ix.cmds.SetShadingLayerRulesProperty(str(shading_layer), [i], "clip_map",
                                                 [str(atlas_surface.get('opacity'))])
        if atlas_surface.get('displacement') and i in ATLAS_LOD_DISPLACEMENT_LEVELS and use_displacement:
            ix.cmds.SetShadingLayerRulesProperty(str(shading_layer), [i], "displacement",
                                                 [str(atlas_surface.get('displacement_map'))])

        group = ix.cmds.CreateObject(asset_name + "_LOD" + str(i) + GROUP_SUFFIX, "Group", "Global",
                                     str(plant_root_ctx))
        group.attrs.inclusion_rule = "./*LOD" + str(i) + "*"
        ix.cmds.AddValues([group.get_full_name() + ".filter"], ["GeometryAbcMesh"])
        ix.cmds.AddValues([group.get_full_name() + ".filter"], ["GeometryPolyfile"])
        ix.cmds.RemoveValue([group.get_full_name() + ".filter"], [2, 0, 1])

    logging.debug("...done setting up shading rules, groups and 3d plant")
    logging.debug("*****************************************************")


def get_json_data_from_directory(directory):
    """Get the JSON data contents required for material setup."""
    logging.debug("Searching for JSON...")
    files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    # Search for any JSON file. Custom Mixer scans don't have a suffix like the ones from the library.
    data = {}
    for f in files:
        filename, extension = os.path.splitext(f)
        if extension == ".json":
            logging.debug("...JSON found!!!")
            json_file = os.path.join(directory, filename + ".json")
            with open(json_file) as json_file:
                json_data = json.load(json_file)
                if not json_data:
                    return None
                meta_data = json_data.get('meta')
                logging.debug("Meta JSON Data: " + str(meta_data))
                if not meta_data:
                    return None
                categories = json_data.get('categories')
                logging.debug("Categories JSON Data: " + str(categories))
                if not categories:
                    return None
                logging.debug("JSON follows Megascans structure.")
                if categories:
                    if 'surface' in categories:
                        data['type'] = 'surface'
                    if '3d' in categories:
                        data['type'] = '3d'
                    if 'atlas' in categories:
                        data['type'] = 'atlas'
                    if '3dplant' in categories:
                        data['type'] = '3dplant'
                if meta_data:
                    for md in meta_data:
                        if md['key'] == "height":
                            data['surface_height'] = float((md['value']).replace("m", "").replace(" ", ""))
                        elif md['key'] == "scanArea":
                            data['scan_area'] = [float(val) for val in
                                                 (md['value']).replace("m", "").replace(" ", "").split("x")]
                        elif md['key'] == "tileable":
                            data['tileable'] = md['value']
            break
    return data


def import_ms_library(library_dir, target_ctx=None, custom_assets=True, skip_categories=(), **kwargs):
    """Imports the whole Megascans Library. Point it to the Downloaded folder inside your library folder.
    """
    logging.debug("Importing Megascans library...")

    ix = get_ix(kwargs.get("ix"))
    if not target_ctx:
        target_ctx = ix.application.get_working_context()
    if not check_context(target_ctx, ix=ix):
        return None
    if not os.path.isdir(library_dir):
        return None
    if os.path.isdir(os.path.join(library_dir, "Downloaded")):
        library_dir = os.path.join(library_dir, "Downloaded")
    logging.debug("Directory set to: " + library_dir)
    print "Scanning folders in " + library_dir

    for category_dir_name in os.listdir(library_dir):
        category_dir_path = os.path.join(library_dir, category_dir_name)
        logging.debug("Checking if directory contains matches keywords: " + category_dir_name)
        if category_dir_name in ["3d", "3dplant", "surface", "surfaces", "atlas", "atlases"]:
            if category_dir_name not in skip_categories and os.path.isdir(category_dir_path):
                context_name = category_dir_name
                if os.path.basename(library_dir) == "My Assets" and category_dir_name == "surfaces":
                    context_name = LIBRARY_MIXER_CTX
                ctx = ix.item_exists(str(target_ctx) + "/" + MEGASCANS_LIBRARY_CATEGORY_PREFIX + context_name)
                if not ctx:
                    ctx = ix.cmds.CreateContext(MEGASCANS_LIBRARY_CATEGORY_PREFIX + context_name,
                                                "Global", str(target_ctx))
                print "Importing library folder: " + category_dir_name
                for asset_directory_name in os.listdir(category_dir_path):
                    asset_directory_path = os.path.join(category_dir_path, asset_directory_name)
                    if os.path.isdir(asset_directory_path):
                        if not ix.item_exists(str(ctx) + "/" + asset_directory_name):
                            print "Importing asset: " + asset_directory_path
                            import_asset(asset_directory_path, target_ctx=ctx, ix=ix)
    if custom_assets and os.path.isdir(os.path.join(library_dir, "My Assets")):
        logging.debug("My Assets exists...")
        import_ms_library(os.path.join(library_dir, "My Assets"), target_ctx=target_ctx,
                          skip_categories=skip_categories, custom_assets=False, ix=ix)
