from clarisse_survival_kit.utility import *

PROJECTIONS = ['planar', 'cylindrical', 'spherical', 'cubic', 'camera', 'parametric', 'uv']


class Surface:
    def __init__(self, ix, **kwargs):
        self.ix = ix
        self.ctx = None
        self.name = None
        self.mtl = None
        self.projection = kwargs.get('projection')
        self.uv_scale = kwargs.get('uv_scale')
        self.object_space = kwargs.get('object_space', 0)
        self.ior = kwargs.get('ior', DEFAULT_IOR)
        self.metallic_ior = kwargs.get('metallic_ior', DEFAULT_METALLIC_IOR)
        self.specular_strength = kwargs.get('specular_strength', DEFAULT_SPECULAR_STRENGTH)
        self.height = kwargs.get('height', DEFAULT_DISPLACEMENT_HEIGHT)
        self.triplanar_blend = kwargs.get('triplanar_blend', 0.5)
        self.tile = kwargs.get('tile', True)
        self.double_sided = kwargs.get('double_sided', False)
        self.textures = {}
        self.streamed_maps = []
        self.displacement_offset = kwargs.get('displacement_offset', 0.5)

    def create_mtl(self, name, target_ctx):
        """Creates a new PhysicalStandard material and context."""
        logging.debug("Creating material...")
        self.name = name
        ctx = self.ix.cmds.CreateContext(name, "Global", str(target_ctx))
        self.ctx = ctx
        mtl = self.ix.cmds.CreateObject(name + MATERIAL_SUFFIX, "MaterialPhysicalStandard", "Global", str(ctx))
        if mtl.attribute_exists('sidedness') and self.double_sided:
            self.ix.cmds.SetValues([str(mtl) + ".sidedness"], ["1"])
        self.ix.cmds.SetValue(str(mtl) + ".specular_1_index_of_refraction", [str(self.ior)])
        self.ix.cmds.SetValue(str(mtl) + ".specular_1_strength", [str(self.specular_strength)])
        self.mtl = mtl
        logging.debug("...done creating material")
        return mtl

    def create_textures(self, textures, color_spaces, streamed_maps=(), clip_opacity=True):
        """Creates all textures from a index:filename dict."""
        logging.debug("Creating textures...")
        for index, texture_settings in TEXTURE_SETTINGS.items():
            if index in textures:
                if index == 'opacity' and clip_opacity:
                    texture_settings['connection'] = None
                logging.debug("Using these settings for texture: " + str(texture_settings))
                color_space = color_spaces.get(index)
                filename = textures[index]
                tx = self.create_tx(index, filename, color_space=color_space,
                                    streamed=index in streamed_maps, **texture_settings)
        logging.debug("...done creating textures")

    def update_textures(self, textures, color_spaces, streamed_maps=()):
        logging.debug("Updating textures...")
        for index, texture_settings in TEXTURE_SETTINGS.items():
            if index in textures:
                logging.debug("Using these settings for texture: " + str(texture_settings))
                color_space = color_spaces.get(index)
                filename = textures[index]
                tx = self.update_tx(index, filename, color_space=color_space,
                                    streamed=index in streamed_maps, **texture_settings)
        logging.debug("...done updating textures")

    def load(self, ctx):
        """Loads and setups the material from an existing context."""
        logging.debug("Loading surface...")
        self.ctx = ctx
        self.name = os.path.basename(str(ctx))
        textures = {}

        ctx_members = get_items(ctx, ix=self.ix)

        mtl = None
        triplanar = False
        for ctx_member in ctx_members:
            logging.debug("Checking ctx member" + str(ctx_member))
            if (ctx_member.is_kindof("TextureMapFile") or ctx_member.is_kindof("TextureStreamedMapFile")) \
                    and ctx_member.is_local():
                self.projection = PROJECTIONS[ctx_member.attrs.projection[0]]
                self.object_space = ctx_member.attrs.object_space[0]
                self.uv_scale = [ctx_member.attrs.uv_scale[0], ctx_member.attrs.uv_scale[2]]
            if ctx_member.is_kindof("MaterialPhysicalStandard"):
                if ctx_member.is_local() or not mtl:
                    mtl = ctx_member
                    logging.debug("Material found:" + str(mtl))
            for key, suffix in SUFFIXES.iteritems():
                if ctx_member.get_contextual_name().endswith(suffix):
                    textures[key] = ctx_member
                    logging.debug("Texture found with index:" + str(key))
            if ctx_member.is_kindof("Displacement"):
                self.height = ctx_member.attrs.front_value[0]
                logging.debug("Displacement found:" + str(ctx_member))
            if ctx_member.get_contextual_name().endswith(TRIPLANAR_SUFFIX):
                triplanar = True
                logging.debug("Triplanar tx found:" + str(ctx_member))
                for key, suffix in SUFFIXES.iteritems():
                    if ctx_member.get_contextual_name().endswith(suffix + TRIPLANAR_SUFFIX):
                        textures[key + '_triplanar'] = ctx_member
            if ctx_member.get_contextual_name().endswith(SINGLE_CHANNEL_SUFFIX):
                for key, suffix in SUFFIXES.iteritems():
                    if ctx_member.get_contextual_name().endswith(suffix + SINGLE_CHANNEL_SUFFIX):
                        textures[key + '_reorder'] = ctx_member
                        self.streamed_maps.append(key)
                        logging.debug("Reorder node for stream maps found:" + str(ctx_member))
        if not mtl or not textures:
            self.ix.log_warning("No valid material found.")
            logging.debug("No material or textures found.")
            return None
        if triplanar:
            self.projection = 'triplanar'
        self.textures = textures
        logging.debug("Textures found:" + str(textures))
        self.mtl = mtl
        return mtl

    def update_projection(self, projection="triplanar", uv_scale=DEFAULT_UV_SCALE,
                          triplanar_blend=0.5, object_space=0, tile=True):
        """Updates the projections in each TextureMapFile."""
        print "PROJECTION SET TO: " + projection
        logging.debug("Projection set to:" + projection)
        for key, tx in self.textures.iteritems():
            if (tx.is_kindof("TextureMapFile") or tx.is_kindof("TextureStreamedMapFile")) and tx.is_local():
                if key == "preview":
                    continue
                if projection == "uv":
                    self.ix.cmds.SetValue(str(tx) + ".projection", [str(PROJECTIONS.index('uv'))])
                else:
                    attrs = self.ix.api.CoreStringArray(6)
                    attrs[0] = str(tx) + ".projection"
                    attrs[1] = str(tx) + ".axis"
                    attrs[2] = str(tx) + ".object_space"
                    attrs[3] = str(tx) + ".uv_scale[0]"
                    attrs[4] = str(tx) + ".uv_scale[1]"
                    attrs[5] = str(tx) + ".uv_scale[2]"
                    values = self.ix.api.CoreStringArray(6)
                    values[0] = str(
                        PROJECTIONS.index('cubic') if projection == "triplanar" else PROJECTIONS.index(projection))
                    values[1] = str(1)
                    values[2] = str(object_space)
                    values[3] = str(uv_scale[0])
                    values[4] = str((uv_scale[0] + uv_scale[1]) / 2)
                    values[5] = str(uv_scale[1])
                    self.ix.cmds.SetValues(attrs, values)
                if not tile:
                    repeat_mode = 0 if tx.is_kindof("TextureStreamedMapFile") else 2
                    attrs = self.ix.api.CoreStringArray(2)
                    attrs[0] = str(tx) + ".u_repeat_mode"
                    attrs[1] = str(tx) + ".v_repeat_mode"
                    values = self.ix.api.CoreStringArray(2)
                    values[0] = str(repeat_mode)
                    values[1] = str(repeat_mode)
                    self.ix.cmds.SetValues(attrs, values)
            if (tx.is_kindof("TextureMapFile") or tx.is_kindof("TextureStreamedMapFile")) and \
                    self.projection != "triplanar" and projection == "triplanar":
                tx_to_triplanar(tx, blend=triplanar_blend, object_space=object_space, ix=self.ix)
            if tx.is_kindof("TextureTriplanar") and projection != "triplanar":
                input_tx = self.ix.get_item(str(tx) + ".right").get_texture()
                replace_connections(input_tx, tx, ignored_attributes=['runtime_materials', ], ix=self.ix)
                self.ix.cmds.DeleteItems([str(tx)])
        self.projection = projection
        self.object_space = object_space
        self.uv_scale = uv_scale
        self.triplanar_blend = triplanar_blend
        logging.debug("Done changing projections")

    def pre_create_tx(self, index):
        """"Gets called before creating textures. Returning False will block the textures from being created."""
        if index == 'gloss':
            if self.get('roughness'):
                return False
        if index == 'bump':
            if self.get('normal'):
                return False
        if index == 'ior':
            if self.get("f0") or self.get("metallic"):
                return False
            if not self.mtl.get_attribute('specular_1_index_of_refraction').is_editable():
                self.ix.cmds.SetValue(str(self.mtl) + ".specular_1_fresnel_mode", [str(0)])
        elif index == "f0":
            if self.get("ior") or self.get("metallic"):
                return False
            if not self.mtl.get_attribute('specular_1_fresnel_reflectivity').is_editable():
                self.ix.cmds.SetValue(str(self.mtl) + ".specular_1_fresnel_mode", [str(1)])
        elif index == "metallic":
            if self.get("ior") or self.get("f0"):
                return False
            if not self.mtl.get_attribute('specular_1_index_of_refraction').is_editable():
                self.ix.cmds.SetValue(str(self.mtl) + ".specular_1_fresnel_mode", [str(0)])
        if index == "emissive":
            self.ix.cmds.SetValue(str(self.mtl) + ".emission_strength", [str(1)])
            self.ix.application.check_for_events()
        if index == 'translucency':
            self.ix.cmds.SetValue(str(self.mtl) + ".diffuse_back_strength", [str(1)])
            self.ix.application.check_for_events()
        return True

    def create_sub_ctx(self, index):
        """"Assigns or creates the context for this specific texture."""
        assigned_ctx = None
        for key, texture_indices in TEXTURE_CONTEXTS.iteritems():
            if index in texture_indices:
                assigned_ctx = key
        if assigned_ctx:
            sub_ctx = self.get_sub_ctx(index)
            if sub_ctx:
                return sub_ctx
            else:
                return self.ix.cmds.CreateContext(assigned_ctx, "Global", str(self.ctx))
        else:
            return self.ctx

    def get_sub_ctx(self, index):
        """"Returns the sub context."""
        for key, texture_indices in TEXTURE_CONTEXTS.iteritems():
            if index in texture_indices:
                ctx_path = str(self.ctx) + "/" + key
                if self.ix.item_exists(ctx_path):
                    return self.ix.get_item(ctx_path)
        return None

    def create_tx(self, index, filename, suffix="_tx", color_space=None, streamed=False, single_channel=False,
                  invert=False,
                  connection=None):
        """Creates a new map or streaming file and if projection is set to triplanar it will be mapped that way."""
        if not self.pre_create_tx(index):
            return None
        triplanar_tx = None
        reorder_tx = None
        logging.debug("create_tx called with arguments:" +
                      "\n".join(
                          [index, filename, suffix, str(color_space), str(streamed), str(single_channel),
                           str(connection)]))
        target_ctx = self.create_sub_ctx(index)
        if streamed:
            logging.debug("Setting up TextureStreamedMapFile...")
            tx = self.ix.cmds.CreateObject(self.name + suffix, "TextureStreamedMapFile", "Global", str(target_ctx))
            udim_file = re.sub(r"((?<!\d)\d{4}(?!\d))", "<UDIM>", os.path.split(filename)[-1], count=1)
            filename = os.path.join(os.path.split(filename)[0], udim_file)
            self.streamed_maps.append(index)
            if single_channel:
                logging.debug("Creating reorder node...")
                reorder_tx = self.ix.cmds.CreateObject(self.name + suffix + SINGLE_CHANNEL_SUFFIX, "TextureReorder",
                                                       "Global", str(target_ctx))
                self.ix.cmds.SetValue(str(reorder_tx) + ".channel_order[0]", ["rrr1"])
                self.ix.cmds.SetTexture([str(reorder_tx) + ".input"], str(tx))
                self.textures[index + '_reorder'] = reorder_tx
        else:
            logging.debug("Setting up TextureMapFile...")
            tx = self.ix.cmds.CreateObject(self.name + suffix, "TextureMapFile", "Global", str(target_ctx))
            if index == 'preview':
                logging.debug("Done creating preview tx: " + str(tx))
                self.ix.cmds.SetValue(str(tx) + ".filename", [filename])
                self.textures[index] = tx
                return tx
        if self.projection != 'uv':
            attrs = self.ix.api.CoreStringArray(6)
            attrs[0] = str(tx) + ".projection"
            attrs[1] = str(tx) + ".axis"
            attrs[2] = str(tx) + ".object_space"
            attrs[3] = str(tx) + ".uv_scale[0]"
            attrs[4] = str(tx) + ".uv_scale[1]"
            attrs[5] = str(tx) + ".uv_scale[2]"
            values = self.ix.api.CoreStringArray(6)
            values[0] = str(
                PROJECTIONS.index('cubic') if self.projection == "triplanar" else PROJECTIONS.index(self.projection))
            values[1] = str(1)
            values[2] = str(self.object_space)
            values[3] = str(self.uv_scale[0])
            values[4] = str((self.uv_scale[0] + self.uv_scale[1]) / 2)
            values[5] = str(self.uv_scale[1])
            self.ix.cmds.SetValues(attrs, values)
        if self.projection == "triplanar":
            logging.debug("Set up triplanar...")
            triplanar_tx = self.ix.cmds.CreateObject(tx.get_contextual_name() + TRIPLANAR_SUFFIX, "TextureTriplanar",
                                                     "Global", str(target_ctx))
            self.ix.cmds.SetTexture([str(triplanar_tx) + ".right"], str(reorder_tx if reorder_tx else tx))
            self.ix.cmds.SetTexture([str(triplanar_tx) + ".left"], str(reorder_tx if reorder_tx else tx))
            self.ix.cmds.SetTexture([str(triplanar_tx) + ".top"], str(reorder_tx if reorder_tx else tx))
            self.ix.cmds.SetTexture([str(triplanar_tx) + ".bottom"], str(reorder_tx if reorder_tx else tx))
            self.ix.cmds.SetTexture([str(triplanar_tx) + ".front"], str(reorder_tx if reorder_tx else tx))
            self.ix.cmds.SetTexture([str(triplanar_tx) + ".back"], str(reorder_tx if reorder_tx else tx))
            self.ix.cmds.SetValue(str(triplanar_tx) + ".blend", [str(self.triplanar_blend)])
            self.ix.cmds.SetValue(str(triplanar_tx) + ".object_space", [str(self.object_space)])
            self.textures[index + '_triplanar'] = triplanar_tx
        default_repeat_mode = 3 if streamed else 0
        attrs = self.ix.api.CoreStringArray(5 if streamed else 6)
        attrs[0] = str(tx) + ".color_space_auto_detect"
        attrs[1] = str(tx) + ".filename"
        attrs[2] = str(tx) + ".invert"
        attrs[3] = str(tx) + ".u_repeat_mode"
        attrs[4] = str(tx) + ".v_repeat_mode"
        values = self.ix.api.CoreStringArray(5 if streamed else 6)
        values[0] = '0'
        values[1] = str(filename)
        values[2] = str(1 if invert else 0)
        values[3] = str((2 if not self.tile else default_repeat_mode))
        values[4] = str((2 if not self.tile else default_repeat_mode))
        if not streamed:
            attrs[5] = str(tx) + ".single_channel_file_behavior"
            values[5] = str((1 if single_channel else 0))
        self.ix.cmds.SetValues(attrs, values)
        self.ix.application.check_for_events()
        extension = os.path.splitext(filename)[-1].strip('.')
        if not color_space or single_channel:
            self.ix.cmds.SetValue(str(tx) + ".use_raw_data", [str(1)])
        else:
            self.ix.cmds.SetValue(str(tx) + ".file_color_space", [str(color_space)])
        self.textures[index] = tx
        if connection:
            if self.projection == "triplanar":
                self.ix.cmds.SetTexture([str(self.mtl) + '.' + connection], str(triplanar_tx))
            else:
                self.ix.cmds.SetTexture([str(self.mtl) + '.' + connection], str(reorder_tx if reorder_tx else tx))
        self.post_create_tx(index, tx)
        logging.debug("Done creating tx: " + str(tx))
        return tx

    def post_create_tx(self, index, tx):
        """Creates certain files at the end of the create_tx function call."""
        logging.debug("Post create function called for: " + index)
        post_tx = None
        if index == "ao":
            post_tx = self.create_ao_blend()
        elif index == "cavity":
            post_tx = self.create_cavity_blend()
        elif index == "displacement":
            post_tx = self.create_displacement_map()
        elif index == "normal":
            post_tx = self.create_normal_map()
        elif index == "bump":
            post_tx = self.create_bump_map()
        elif index == "ior":
            post_tx = self.create_ior_divide_tx()
        elif index == "metallic":
            post_tx = self.create_metallic_blend_tx()
        logging.debug("Post texture: " + str(post_tx))
        return post_tx

    def create_displacement_map(self):
        """Creates a Displacement map if it doesn't exist."""
        logging.debug("Creating displacement map...")
        if not self.get('displacement'):
            self.ix.log_warning("No displacement texture was found.")
            return None
        if self.projection == 'triplanar':
            disp_tx = self.get('displacement_triplanar')
        else:
            if self.get('displacement_reorder'):
                disp_tx = self.get('displacement_reorder')
            else:
                disp_tx = self.get('displacement')
        disp_offset_tx = self.ix.cmds.CreateObject(self.name + DISPLACEMENT_OFFSET_SUFFIX, "TextureSubtract",
                                                   "Global", str(self.get_sub_ctx('displacement')))
        self.ix.cmds.SetTexture([str(disp_offset_tx) + ".input1"], str(disp_tx))
        self.ix.cmds.SetValues([str(disp_offset_tx) + ".input2"], [str(self.displacement_offset)])
        disp_height_scale_tx = self.ix.cmds.CreateObject(self.name + DISPLACEMENT_HEIGHT_SCALE_SUFFIX,
                                                         "TextureMultiply", "Global",
                                                         str(self.get_sub_ctx('displacement')))
        self.ix.cmds.SetTexture([str(disp_height_scale_tx) + ".input1"], str(disp_offset_tx))
        self.ix.cmds.SetValues([str(disp_height_scale_tx) + ".input2"],
                               [str(self.height)])
        disp = self.ix.cmds.CreateObject(self.name + DISPLACEMENT_MAP_SUFFIX, "Displacement",
                                         "Global", str(self.ctx))
        attrs = self.ix.api.CoreStringArray(3)
        attrs[0] = str(disp) + ".bound[0]"
        attrs[1] = str(disp) + ".bound[1]"
        attrs[2] = str(disp) + ".bound[2]"
        values = self.ix.api.CoreStringArray(3)
        values[0] = str(self.height)
        values[1] = str(self.height)
        values[2] = str(self.height)
        self.ix.cmds.SetValues(attrs, values)
        self.ix.cmds.SetTexture([str(disp) + ".front_value"], str(disp_height_scale_tx))
        self.textures['displacement_map'] = disp
        return disp

    def create_normal_map(self):
        """Creates a Normal map if it doesn't exist."""
        logging.debug("Creating normal map...")
        if not self.get('normal'):
            self.ix.log_warning("No normal texture was found.")
            return None
        if self.projection == 'triplanar':
            normal_tx = self.get('normal_triplanar')
        else:
            normal_tx = self.get('normal')
        normal_map = self.ix.cmds.CreateObject(self.name + NORMAL_MAP_SUFFIX, "TextureNormalMap",
                                               "Global", str(self.get_sub_ctx('normal')))
        self.ix.cmds.SetTexture([str(normal_map) + ".input"], str(normal_tx))
        self.ix.cmds.SetTexture([str(self.mtl) + ".normal_input"], str(normal_map))
        self.textures['normal_map'] = normal_map
        return normal_map

    def create_ao_blend(self):
        """Creates a AO blend texture if it doesn't exist."""
        logging.debug("Creating ao blend texture...")
        if not self.get('ao'):
            self.ix.log_warning("No ao texture was found.")
            return None
        ao_tx = self.get_out_tx('ao')
        if not ao_tx:
            print 'ERROR: AO could not be properly created.'
            logging.error('ERROR: AO could not be properly created.')
            return False
        diffuse_tx = self.get_out_tx('diffuse')
        logging.debug('Hooking ao to: ' + str(diffuse_tx))
        ao_blend_tx = self.ix.cmds.CreateObject(self.name + OCCLUSION_BLEND_SUFFIX, "TextureBlend", "Global",
                                                str(self.get_sub_ctx('diffuse')))
        self.ix.cmds.SetTexture([str(ao_blend_tx) + ".input2"], str(diffuse_tx))
        self.ix.cmds.SetTexture([str(ao_blend_tx) + ".input1"], str(ao_tx))
        self.ix.cmds.SetValue(str(ao_blend_tx) + ".mode", [str(7)])
        self.ix.cmds.SetValue(str(ao_blend_tx) + ".mix", [str(DEFAULT_AO_BLEND_STRENGTH)])
        self.ix.cmds.SetTexture([str(self.mtl) + ".diffuse_front_color"], str(ao_blend_tx))
        self.textures["ao_blend"] = ao_blend_tx
        return ao_blend_tx

    def create_cavity_blend(self):
        """Creates a cavity blend texture if it doesn't exist."""
        logging.debug("Creating cavity blend texture...")
        if not self.get('cavity'):
            self.ix.log_warning("No cavity texture was found.")
            return None
        cavity_tx = self.get_out_tx('cavity')
        if not cavity_tx:
            print 'ERROR: CAVITY could not be properly created.'
            logging.error('ERROR: CAVITY could not be properly created.')
            return False
        diffuse_tx = self.get_out_tx('diffuse')
        logging.debug('Hooking cavity to: ' + str(diffuse_tx))
        cavity_remap_tx = self.ix.cmds.CreateObject(self.name + CAVITY_REMAP_SUFFIX, "TextureRemap",
                                                    "Global", str(self.get_sub_ctx('diffuse')))
        self.ix.cmds.SetTexture([str(cavity_remap_tx) + ".input"], str(cavity_tx))
        cavity_blend_tx = self.ix.cmds.CreateObject(self.name + CAVITY_BLEND_SUFFIX, "TextureBlend", "Global",
                                                    str(self.get_sub_ctx('diffuse')))
        self.ix.cmds.SetTexture([str(cavity_blend_tx) + ".input2"], str(diffuse_tx))
        self.ix.cmds.SetTexture([str(cavity_blend_tx) + ".input1"], str(cavity_remap_tx))
        self.ix.cmds.SetValue(str(cavity_blend_tx) + ".mode", [str(7)])
        self.ix.cmds.SetValue(str(cavity_blend_tx) + ".mix", [str(DEFAULT_CAVITY_BLEND_STRENGTH)])
        self.ix.cmds.SetTexture([str(self.mtl) + ".diffuse_front_color"], str(cavity_blend_tx))
        self.ix.cmds.SetValues([str(cavity_remap_tx) + ".pass_through"], ["1"])
        self.textures["cavity_remap"] = cavity_remap_tx
        self.textures["cavity_blend"] = cavity_blend_tx
        return cavity_blend_tx

    def create_bump_map(self):
        """Creates a Bump map if it doesn't exist."""
        logging.debug("Creating bump map...")
        if not self.get('bump'):
            self.ix.log_warning("No bump texture was found.")
            return None
        bump_tx = self.get_out_tx('bump')
        if not bump_tx:
            print 'ERROR: BUMP could not be properly created.'
            logging.error('ERROR: BUMP could not be properly created.')
            return False

        bump_map = self.ix.cmds.CreateObject(self.name + BUMP_MAP_SUFFIX, "TextureBumpMap",
                                             "Global", str(self.get_sub_ctx('bump')))
        self.ix.cmds.SetTexture([str(bump_map) + ".input"], str(bump_tx))
        self.ix.cmds.SetTexture([str(self.mtl) + ".normal_input"], str(bump_map))
        self.textures['bump_map'] = bump_map
        return bump_map

    def create_ior_divide_tx(self):
        """Creates an IOR divide helper texture if it doesn't exist."""
        logging.debug("Creating IOR divide texture...")
        if not self.get('ior'):
            self.ix.log_warning("No ior texture was found.")
            return None
        ior_tx = self.get_out_tx('ior')
        if not ior_tx:
            print 'ERROR: IOR could not be properly created.'
            logging.error('ERROR: IOR could not be properly created.')
            return False

        logging.debug("Using following texture as input2 for divide: " + str(ior_tx))
        ior_divide_tx = self.ix.cmds.CreateObject(self.name + IOR_DIVIDE_SUFFIX, "TextureDivide",
                                                  "Global", str(self.get_sub_ctx('ior')))
        ior_divide_tx.attrs.input1[0] = 1.0
        ior_divide_tx.attrs.input1[1] = 1.0
        ior_divide_tx.attrs.input1[2] = 1.0
        self.ix.cmds.SetTexture([str(ior_divide_tx) + ".input2"], str(ior_tx))
        self.ix.application.check_for_events()
        self.textures['ior_divide'] = ior_divide_tx
        if self.mtl.get_attribute('specular_1_index_of_refraction').is_editable():
            self.ix.cmds.SetTexture([str(self.mtl) + ".specular_1_index_of_refraction"], str(ior_divide_tx))
            self.ix.application.check_for_events()
        else:
            logging.debug("IOR was locked")
        return ior_divide_tx

    def create_metallic_blend_tx(self):
        """Creates an IOR blend helper texture if it doesn't exist."""
        logging.debug("Creating IOR blend texture...")
        if not self.get('metallic'):
            self.ix.log_warning("No ior texture was found.")
            return None
        metallic_tx = self.get_out_tx('metallic')
        if not metallic_tx:
            print 'ERROR: METALLIC could not be properly created.'
            logging.error('ERROR: METALLIC could not be properly created.')
            return False

        metallic_blend_tx = self.ix.cmds.CreateObject(self.name + METALLIC_BLEND_SUFFIX, "TextureBlend",
                                                      "Global", str(self.get_sub_ctx('ior')))
        metallic_blend_tx.attrs.input2[0] = self.ior
        metallic_blend_tx.attrs.input2[1] = self.ior
        metallic_blend_tx.attrs.input2[2] = self.ior
        metallic_blend_tx.attrs.input1[0] = self.metallic_ior
        metallic_blend_tx.attrs.input1[1] = self.metallic_ior
        metallic_blend_tx.attrs.input1[2] = self.metallic_ior
        self.ix.cmds.SetTexture([str(metallic_blend_tx) + ".mix"], str(self.get('metallic')))
        self.ix.application.check_for_events()
        self.textures['metallic_blend'] = metallic_blend_tx
        if self.mtl.get_attribute('specular_1_index_of_refraction').is_editable():
            self.ix.cmds.SetTexture([str(self.mtl) + ".specular_1_index_of_refraction"], str(metallic_blend_tx))
            self.ix.application.check_for_events()
        else:
            logging.debug("IOR was locked")
        return metallic_blend_tx

    def update_ior(self, ior, metallic_ior=DEFAULT_METALLIC_IOR):
        """Updates the IOR.
        Make sure floats have 1 precision. 1.6 will work, but 1.65 will crash Clarisse.
        """
        logging.debug("Updating IOR...")
        if self.mtl.get_attribute('specular_1_index_of_refraction').is_editable():
            self.ix.cmds.SetValue(str(self.mtl) + ".specular_1_index_of_refraction", [str(ior)])
            self.ix.application.check_for_events()
            self.ior = ior
        else:
            logging.debug("IOR was locked")

    def get_out_tx(self, index):
        if index == 'diffuse' and self.get('cavity_blend'):
            tx = self.get('cavity_blend')
        elif index == 'diffuse' and self.get('ao_blend'):
            tx = self.get('ao_blend')
        elif self.projection == 'triplanar':
            tx = self.get(index + '_triplanar')
        else:
            tx = self.get(index + '_reorder', index)
        return tx

    def update_tx(self, index, filename, suffix, color_space, streamed=False, single_channel=False,
                  invert=False, connection=None):
        """Updates a texture by changing the filename or color space settings."""
        logging.debug("update_tx called with arguments:" +
                      "\n".join([index, filename, suffix, str(color_space), str(streamed), str(single_channel)]))
        tx = self.get(index)
        if tx.is_kindof("TextureStreamedMapFile") != streamed:
            logging.debug("Map is no longer Map file or Stream Map. Switch in progress...")
            self.destroy_tx(index)
            self.create_tx(index, filename, suffix, streamed=streamed, single_channel=single_channel,
                           invert=invert, connection=connection)
            logging.debug("Texture recreated as: " + str(self.get(index)))
            tx = self.get(index)
        attrs = self.ix.api.CoreStringArray(2 if streamed else 3)
        attrs[0] = str(tx) + ".filename"
        attrs[1] = str(tx) + ".invert"
        values = self.ix.api.CoreStringArray(2 if streamed else 3)
        values[0] = filename
        values[1] = str((1 if invert else 0))
        extension = os.path.splitext(filename)[-1].strip('.')
        if not streamed:
            attrs[2] = str(tx) + ".single_channel_file_behavior"
            values[2] = str((1 if single_channel else 0))
        self.ix.cmds.SetValues(attrs, values)

        if not color_space or single_channel:
            self.ix.cmds.SetValue(str(tx) + ".use_raw_data", [str(1)])
        else:
            self.ix.cmds.SetValue(str(tx) + ".use_raw_data", [str(0)])
            self.ix.application.check_for_events()
            self.ix.cmds.SetValues([str(color_space)], [str(tx) + ".file_color_space"])

        if connection:
            tx_attr = self.mtl.get_attribute(connection).get_texture()
            if not tx_attr:
                connection_tx = self.get_out_tx(index)
                self.ix.cmds.SetTexture([str(self.mtl) + '.' + connection], str(connection_tx))
        return tx

    def update_displacement(self, height, displacement_offset=0.5):
        """Updates a Displacement map with new height settings."""
        logging.debug("Updating displacement...")
        disp = self.get('displacement_map')
        if disp:
            attrs = self.ix.api.CoreStringArray(3)
            attrs[0] = str(disp) + ".bound[0]"
            attrs[1] = str(disp) + ".bound[1]"
            attrs[2] = str(disp) + ".bound[2]"
            values = self.ix.api.CoreStringArray(3)
            values[0] = str(height)
            values[1] = str(height)
            values[2] = str(height)
            self.ix.cmds.SetValues(attrs, values)
            if disp.attrs.front_value[0] != 1:
                disp.attrs.front_value = height
            if disp.attrs.front_offset[0] != 0:
                disp.attrs.front_offset = displacement_offset * -1
        self.height = height
        self.displacement_offset = displacement_offset
        connected_txs = get_textures_connected_to_texture(self.get_out_tx('displacement'), ix=self.ix)
        for connected_tx in connected_txs:
            if connected_tx.get_contextual_name().endswith(DISPLACEMENT_HEIGHT_SCALE_SUFFIX):
                connected_tx.attrs.input2[0] = height
                connected_tx.attrs.input2[1] = height
                connected_tx.attrs.input2[2] = height
            elif connected_tx.get_contextual_name().endswith(DISPLACEMENT_OFFSET_SUFFIX):
                connected_tx.attrs.input2[0] = displacement_offset
                connected_tx.attrs.input2[1] = displacement_offset
                connected_tx.attrs.input2[2] = displacement_offset

    def update_opacity(self, clip_opacity, found_textures, update_textures):
        """Connect/Disconnect the opacity texture depending if clip_opacity is set to False/True."""
        logging.debug("Updating opacity...")
        if 'opacity' in update_textures and 'opacity' in found_textures:
            if clip_opacity and self.ix.get_item(str(self.mtl) + '.opacity').get_texture():
                self.ix.cmds.SetTexture([str(self.mtl) + ".opacity"], '')
            elif not clip_opacity and not self.ix.get_item(str(self.mtl) + '.opacity').get_texture():
                self.ix.cmds.SetTexture([str(self.mtl) + ".opacity"], str(self.get('opacity')))

    def update_names(self, name):
        """Updates all texture names used in the context."""
        logging.debug("Updating names...")
        self.ix.cmds.RenameItem(str(self.ctx), name)

        ctx_members = get_items(self.ctx, ix=self.ix)

        for ctx_member in ctx_members:
            if ctx_member.is_editable() and not ctx_member.is_content_locked():
                logging.debug(
                    "Updating name from " + str(ctx_member) + " to " +
                    ctx_member.get_contextual_name().replace(self.name, name))
                self.ix.cmds.RenameItem(str(ctx_member), ctx_member.get_contextual_name().replace(self.name, name))
            else:
                logging.debug('Ctx member %s was locked' % str(ctx_member))
        disp_tx = self.get_out_tx('displacement')
        if disp_tx:
            logging.debug('Updating mixes names if they exist')
            connected_txs = get_textures_connected_to_texture(disp_tx, ix=self.ix)
            for connected_tx in connected_txs:
                if connected_tx.get_contextual_name().endswith(DISPLACEMENT_HEIGHT_SCALE_SUFFIX):
                    mix_ctx = connected_tx.get_context()
                    self.ix.cmds.RenameItem(str(mix_ctx.get_parent()), name + MIX_SUFFIX)
                    mix_ctx_members = get_items(mix_ctx.get_parent(), ix=self.ix)

                    for ctx_member in mix_ctx_members:
                        if ctx_member.is_editable() and not ctx_member.is_content_locked():
                            logging.debug(
                                "Updating name from " + str(ctx_member) + " to " +
                                ctx_member.get_contextual_name().replace(self.name, name))
                            self.ix.cmds.RenameItem(str(ctx_member),
                                                    ctx_member.get_contextual_name().replace(self.name, name))
                        else:
                            logging.debug('Ctx member %s was locked' % str(ctx_member))
        self.name = name

    def destroy_tx(self, index):
        """Removes a texture and its pair."""
        logging.debug("Removing the following index from material: " + index)
        if index == 'displacement':
            self.destroy_tx('displacement_map')
        elif index == 'normal':
            self.destroy_tx('normal_map')
        elif index == 'bump':
            self.destroy_tx('bump_map')
        elif index == 'ior':
            self.destroy_tx('ior_divide')
        elif index == 'ao':
            self.destroy_tx('ao_blend')
        elif index == 'cavity':
            self.destroy_tx('cavity_remap')
            self.destroy_tx('cavity_blend')

        if self.get(index + '_reorder'):
            self.destroy_tx(index + '_reorder')
        # Remove triplanar pair. If texture is triplanar avoid infinite recursion.
        if self.projection == 'triplanar' and not index.endswith('_triplanar'):
            self.destroy_tx(index + "_triplanar")
        self.ix.cmds.DeleteItems([str(self.get(index))])
        self.textures.pop(index, None)
        logging.debug("Done removing: " + index)

    def get(self, index, fallback=None):
        """Returns a texture."""
        tx = self.textures.get(index)
        if not tx and fallback:
            tx = self.get(fallback)
        return tx

    def clean(self):
        """Resets the emissive or translucency attributes to 0 when not used."""
        logging.debug("Cleanup...")
        if not self.get('emissive'):
            logging.debug("Resetting emission...")
            self.ix.cmds.SetValue(str(self.mtl) + ".emission_strength", [str(0)])
        if not self.get('translucency'):
            logging.debug("Resetting translucency...")
            self.ix.cmds.SetValue(str(self.mtl) + ".diffuse_back_strength", [str(0)])
        sub_ctxs = get_sub_contexts(self.ctx)
        for sub_ctx in sub_ctxs:
            logging.debug("Cleaning up empty ctx: " + str(sub_ctx))
            if sub_ctx.get_object_count() == 0:
                self.ix.cmds.DeleteItems([str(sub_ctx)])
