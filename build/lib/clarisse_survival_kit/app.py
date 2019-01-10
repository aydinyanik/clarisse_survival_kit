import json

from clarisse_survival_kit.selectors import *
from clarisse_survival_kit.utility import *
# Global variable
from clarisse_survival_kit.utility import get_textures_from_directory, get_mtl_from_context, get_disp_from_context, \
	get_attrs_connected_to_texture, check_selection, check_context

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
		self.height = kwargs.get('height', DEFAULT_DISPLACEMENT_HEIGHT)
		self.triplanar_blend = kwargs.get('triplanar_blend', 0.5)
		self.tile = kwargs.get('tile', True)
		self.textures = {}

	def create_mtl(self, name, target_ctx):
		"""Creates a new PhysicalStandard material and context."""
		self.name = name
		ctx = self.ix.cmds.CreateContext(name, "Global", str(target_ctx))
		self.ctx = ctx
		mtl = self.ix.cmds.CreateObject(name + MATERIAL_SUFFIX, "MaterialPhysicalStandard", "Global", str(ctx))
		self.ix.cmds.SetValue(str(mtl) + ".specular_1_index_of_refraction", [str(self.ior)])
		self.mtl = mtl
		return mtl

	def create_textures(self, textures, srgb, clip_opacity=True):
		"""Creates all textures from a dict. Indices that are in the srgb list will be set to srgb else linear."""
		if 'diffuse' in textures:
			diffuse_tx = self.create_tx(index='diffuse', filename=textures.get('diffuse'), suffix=DIFFUSE_SUFFIX,
										connection="diffuse_front_color", srgb=('diffuse' in srgb))
		if 'displacement' in textures:
			displacement_tx = self.create_tx(index='displacement', filename=textures.get('displacement'),
											 suffix=DISPLACEMENT_SUFFIX,
											 srgb=('displacement' in srgb), single_channel=True)
			self.create_displacement_map()
		if 'specular' in textures:
			specular_tx = self.create_tx(index='specular', filename=textures.get('specular'),
										 suffix=SPECULAR_COLOR_SUFFIX,
										 srgb=('specular' in srgb), connection="specular_1_color")
		if 'roughness' in textures or 'gloss' in textures:
			roughness_tx = self.create_tx(index='roughness', filename=textures.get('roughness', textures.get('gloss')),
										  suffix=SPECULAR_ROUGHNESS_SUFFIX,
										  srgb=('roughness' in srgb), single_channel=True,
										  invert=('roughness' not in textures),
										  connection="specular_1_roughness")
		if 'normal' in textures:
			normal_tx = self.create_tx(index='normal', filename=textures.get('normal'),
									   suffix=NORMAL_SUFFIX, srgb=('normal' in srgb))
			self.create_normal_map()
		elif 'bump' in textures:
			bump_tx = self.create_tx(index='bump', filename=textures.get('bump'),
									 suffix=BUMP_SUFFIX, srgb=('bump' in srgb), single_channel=True)
			self.create_bump_map()
		if 'opacity' in textures:
			opacity_tx = self.create_tx(index='opacity', filename=textures.get('opacity'),
										suffix=OPACITY_SUFFIX,
										srgb=('opacity' in srgb), single_channel=True,
										connection=None if clip_opacity else "opacity")
		if 'translucency' in textures:
			self.ix.cmds.SetValue(str(self.mtl) + ".diffuse_back_strength", [str(1)])
			translucency_tx = self.create_tx(index='translucency', filename=textures.get('translucency'),
											 suffix=TRANSLUCENCY_SUFFIX, srgb=('translucency' in srgb),
											 connection="diffuse_back_color")
		if 'emissive' in textures:
			self.ix.cmds.SetValue(str(self.mtl) + ".emission_strength", [str(1)])
			emissive_tx = self.create_tx(index='emissive', filename=textures.get('emissive'),
										 suffix=EMISSIVE_SUFFIX, srgb=('emissive' in srgb),
										 connection="emission_color")
		if 'ior' in textures:
			ior_tx = self.create_tx(index='ior', filename=textures.get('ior'),
									suffix=IOR_SUFFIX, srgb=('ior' in srgb), single_channel=True)
			self.create_ior_divide_tx()

	def update_textures(self, textures, srgb):
		if 'diffuse' in textures:
			diffuse_tx = self.update_tx(index='diffuse', filename=textures.get('diffuse'), suffix=DIFFUSE_SUFFIX,
										srgb=('diffuse' in srgb))
		if 'displacement' in textures:
			displacement_tx = self.update_tx(index='displacement', filename=textures.get('displacement'),
											 suffix=DISPLACEMENT_SUFFIX,
											 srgb=('displacement' in srgb), single_channel=True)
		if 'specular' in textures:
			specular_tx = self.update_tx(index='specular', filename=textures.get('specular'),
										 suffix=SPECULAR_COLOR_SUFFIX, srgb=('specular' in srgb))
		if 'roughness' in textures or 'gloss' in textures:
			roughness_tx = self.update_tx(index='roughness', filename=textures.get('roughness', textures.get('gloss')),
										  suffix=SPECULAR_ROUGHNESS_SUFFIX,
										  srgb=('roughness' in srgb), single_channel=True,
										  invert=('roughness' not in textures))
		if 'normal' in textures:
			normal_tx = self.update_tx(index='normal', filename=textures.get('normal'),
									   suffix=NORMAL_SUFFIX, srgb=('normal' in srgb))
		elif 'bump' in textures:
			bump_tx = self.update_tx(index='bump', filename=textures.get('bump'),
									 suffix=BUMP_SUFFIX, srgb=('bump' in srgb), single_channel=True)
		if 'opacity' in textures:
			opacity_tx = self.update_tx(index='opacity', filename=textures.get('opacity'),
										suffix=OPACITY_SUFFIX,
										srgb=('opacity' in srgb), single_channel=True)
		if 'translucency' in textures:
			self.ix.cmds.SetValue(str(self.mtl) + ".diffuse_back_strength", [str(1)])
			translucency_tx = self.update_tx(index='translucency', filename=textures.get('translucency'),
											 suffix=TRANSLUCENCY_SUFFIX, srgb=('translucency' in srgb))
		if 'emissive' in textures:
			self.ix.cmds.SetValue(str(self.mtl) + ".emission_strength", [str(1)])
			emissive_tx = self.update_tx(index='emissive', filename=textures.get('emissive'),
										 suffix=EMISSIVE_SUFFIX, srgb=('emissive' in srgb))
		if 'ior' in textures:
			ior_tx = self.update_tx(index='ior', filename=textures.get('ior'),
									suffix=IOR_SUFFIX, srgb=('ior' in srgb), single_channel=True)

	def load(self, ctx):
		"""Loads and setups the material from an existing context."""
		self.ctx = ctx
		self.name = os.path.basename(str(ctx))
		textures = {}

		objects_array = self.ix.api.OfObjectArray(ctx.get_object_count())
		flags = self.ix.api.CoreBitFieldHelper()
		ctx.get_all_objects(objects_array, flags, False)

		mtl = None
		triplanar = False

		for ctx_member in objects_array:
			if ctx_member.is_context():
				continue
			if ctx_member.is_kindof("TextureMapFile") and ctx_member.is_local():
				self.projection = PROJECTIONS[ctx_member.attrs.projection[0]]
				self.object_space = ctx_member.attrs.object_space[0]
				self.uv_scale = [ctx_member.attrs.uv_scale[0], ctx_member.attrs.uv_scale[2]]
			if ctx_member.is_kindof("MaterialPhysicalStandard"):
				if ctx_member.is_local() or not mtl:
					print "MTL FOUND: " + str(ctx_member)
					mtl = ctx_member
			for key, suffix in SUFFIXES.iteritems():
				if ctx_member.get_contextual_name().endswith(suffix):
					textures[key] = ctx_member
			if ctx_member.is_kindof("Displacement"):
				self.height = ctx_member.attrs.front_value[0]
			if ctx_member.get_contextual_name().endswith(TRIPLANAR_SUFFIX):
				triplanar = True
				for key, suffix in SUFFIXES.iteritems():
					if ctx_member.get_contextual_name().endswith(suffix + TRIPLANAR_SUFFIX):
						textures[key + '_triplanar'] = ctx_member
		if not mtl or not textures:
			self.ix.log_warning("No valid material found.")
			return None
		if triplanar:
			self.projection = 'triplanar'
		self.textures = textures
		self.mtl = mtl
		return mtl

	def update_projection(self, projection="triplanar", uv_scale=DEFAULT_UV_SCALE,
						  triplanar_blend=0.5, object_space=0, tile=True):
		"""Updates the projections in each TextureMapFile."""
		print "PROJECTION SET TO: " + projection
		for key, tx in self.textures.iteritems():
			if tx.is_kindof("TextureMapFile") and tx.is_local():
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
					attrs = self.ix.api.CoreStringArray(2)
					attrs[0] = str(tx) + ".u_repeat_mode"
					attrs[1] = str(tx) + ".v_repeat_mode"
					values = self.ix.api.CoreStringArray(2)
					values[0] = str(2)
					values[1] = str(2)
					self.ix.cmds.SetValues(attrs, values)
			if tx.is_kindof("TextureMapFile") and self.projection != "triplanar" and projection == "triplanar":
				tx_to_triplanar(tx, blend=triplanar_blend, object_space=object_space, ix=self.ix)
			if tx.is_kindof("TextureTriplanar") and projection != "triplanar":
				input_tx = self.ix.get_item(str(tx) + ".right").get_texture()
				connected_attrs = self.ix.api.OfAttrVector()
				get_attrs_connected_to_texture(tx, connected_attrs, ix=self.ix)
				for i_attr in range(0, connected_attrs.get_count()):
					self.ix.cmds.SetTexture([str(connected_attrs[i_attr])], str(input_tx))
				self.ix.cmds.DeleteItems([str(tx)])
		self.projection = projection
		self.object_space = object_space
		self.uv_scale = uv_scale
		self.triplanar_blend = triplanar_blend

	def create_tx(self, index, filename, suffix, srgb=True, single_channel=False, invert=False,
				  connection=None):
		"""Creates a new TextureMapFile and if projection is set to triplanar it will be mapped that way."""
		triplanar_tx = None
		color_space = 'Clarisse|sRGB' if srgb else 'linear'

		tx = self.ix.cmds.CreateObject(self.name + suffix, "TextureMapFile", "Global", str(self.ctx))
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
			triplanar_tx = self.ix.cmds.CreateObject(tx.get_contextual_name() + TRIPLANAR_SUFFIX, "TextureTriplanar",
													 "Global", str(self.ctx))
			self.ix.cmds.SetTexture([str(triplanar_tx) + ".right"], str(tx))
			self.ix.cmds.SetTexture([str(triplanar_tx) + ".left"], str(tx))
			self.ix.cmds.SetTexture([str(triplanar_tx) + ".top"], str(tx))
			self.ix.cmds.SetTexture([str(triplanar_tx) + ".bottom"], str(tx))
			self.ix.cmds.SetTexture([str(triplanar_tx) + ".front"], str(tx))
			self.ix.cmds.SetTexture([str(triplanar_tx) + ".back"], str(tx))
			self.ix.cmds.SetValue(str(triplanar_tx) + ".blend", [str(self.triplanar_blend)])
			self.ix.cmds.SetValue(str(triplanar_tx) + ".object_space", [str(self.object_space)])
			self.textures[index + '_triplanar'] = triplanar_tx
		attrs = self.ix.api.CoreStringArray(7)
		attrs[0] = str(tx) + ".color_space_auto_detect"
		attrs[1] = str(tx) + ".file_color_space"
		attrs[2] = str(tx) + ".single_channel_file_behavior"
		attrs[3] = str(tx) + ".filename"
		attrs[4] = str(tx) + ".invert"
		attrs[5] = str(tx) + ".u_repeat_mode"
		attrs[6] = str(tx) + ".v_repeat_mode"
		values = self.ix.api.CoreStringArray(7)
		values[0] = '0'
		values[1] = str(color_space)
		values[2] = str((1 if single_channel else 0))
		values[3] = str(filename)
		values[4] = str((2 if not self.tile else 0))
		values[5] = str((2 if not self.tile else 0))
		self.ix.cmds.SetValues(attrs, values)
		self.textures[index] = tx
		if connection:
			if self.projection == "triplanar":
				self.ix.cmds.SetTexture([str(self.mtl) + "." + connection], str(triplanar_tx))
			else:
				self.ix.cmds.SetTexture([str(self.mtl) + "." + connection], str(tx))
		return tx

	def create_displacement_map(self):
		"""Creates a Displacement map if it doesn't exist."""
		if not self.get('displacement'):
			self.ix.log_warning("No displacement texture was found.")
			return None
		if self.projection == 'triplanar':
			disp_tx = self.get('displacement_triplanar')
		else:
			disp_tx = self.get('displacement')
		disp = self.ix.cmds.CreateObject(self.name + DISPLACEMENT_MAP_SUFFIX, "Displacement",
										 "Global", str(self.ctx))
		attrs = self.ix.api.CoreStringArray(5)
		attrs[0] = str(disp) + ".bound[0]"
		attrs[1] = str(disp) + ".bound[1]"
		attrs[2] = str(disp) + ".bound[2]"
		attrs[3] = str(disp) + ".front_value"
		attrs[4] = str(disp) + ".front_offset"
		values = self.ix.api.CoreStringArray(5)
		values[0] = str(self.height * 1.1)
		values[1] = str(self.height * 1.1)
		values[2] = str(self.height * 1.1)
		values[3] = str(self.height)
		values[4] = str((self.height / 2) * -1)
		self.ix.cmds.SetValues(attrs, values)
		self.ix.cmds.SetTexture([str(disp) + ".front_value"], str(disp_tx))
		self.textures['displacement_map'] = disp
		return disp

	def create_normal_map(self):
		"""Creates a Normal map if it doesn't exist."""
		if not self.get('normal'):
			self.ix.log_warning("No normal texture was found.")
			return None
		if self.projection == 'triplanar':
			normal_tx = self.get('normal_triplanar')
		else:
			normal_tx = self.get('normal')
		normal_map = self.ix.cmds.CreateObject(self.name + NORMAL_MAP_SUFFIX, "TextureNormalMap",
											   "Global", str(self.ctx))
		self.ix.cmds.SetTexture([str(normal_map) + ".input"], str(normal_tx))
		self.ix.cmds.SetTexture([str(self.mtl) + ".normal_input"], str(normal_map))
		self.textures['normal_map'] = normal_map
		return normal_map

	def create_bump_map(self):
		"""Creates a Bump map if it doesn't exist."""
		if not self.get('bump'):
			self.ix.log_warning("No bump texture was found.")
			return None
		if self.projection == 'triplanar':
			bump_tx = self.get('bump_triplanar')
		else:
			bump_tx = self.get('bump')
		bump_map = self.ix.cmds.CreateObject(self.name + BUMP_MAP_SUFFIX, "TextureBumpMap",
											 "Global", str(self.ctx))
		self.ix.cmds.SetTexture([str(bump_map) + ".input"], str(bump_tx))
		self.ix.cmds.SetTexture([str(self.mtl) + ".normal_input"], str(bump_map))
		self.textures['bump_map'] = bump_map
		return bump_map

	def create_ior_divide_tx(self):
		"""Creates an IOR divide helper texture if it doesn't exist."""
		if not self.get('ior'):
			self.ix.log_warning("No ior texture was found.")
			return None
		if self.projection == 'triplanar':
			ior_tx = self.get('ior_triplanar')
		else:
			ior_tx = self.get('ior')
		ior_divide_tx = self.ix.cmds.CreateObject(self.name + IOR_DIVIDE_SUFFIX, "TextureDivide",
												  "Global", str(self.ctx))
		ior_divide_tx.attrs.input1[0] = 1.0
		ior_divide_tx.attrs.input1[1] = 1.0
		ior_divide_tx.attrs.input1[2] = 1.0
		self.ix.cmds.SetTexture([str(ior_tx) + ".input2"], str(ior_tx))
		self.textures['ior_divide'] = ior_divide_tx
		return ior_divide_tx

	def update_ior(self, ior):
		"""Updates the IOR.
		Make sure floats have 1 precision. 1.6 will work, but 1.65 will crash Clarisse.
		"""
		if self.mtl.get_attribute('specular_1_index_of_refraction').is_editable():
			print "IOR MTL: " + str(self.mtl)
			self.ix.cmds.SetValue(str(self.mtl) + ".specular_1_index_of_refraction", [str(ior)])
			self.ior = ior

	def update_tx(self, index, filename, suffix, srgb=True, single_channel=False, invert=False):
		"""Updates a texture by changing the filename or color space settings."""
		tx = self.get(index)
		if srgb:
			color_space = 'Clarisse|sRGB'
		else:
			color_space = 'linear'
		attrs = self.ix.api.CoreStringArray(4)
		attrs[0] = str(tx) + ".file_color_space"
		attrs[1] = str(tx) + ".single_channel_file_behavior"
		attrs[2] = str(tx) + ".filename"
		attrs[3] = str(tx) + ".invert"
		values = self.ix.api.CoreStringArray(4)
		values[0] = color_space
		values[1] = str((1 if single_channel else 0))
		values[2] = filename
		values[3] = str((1 if invert else 0))
		self.ix.cmds.SetValues(attrs, values)
		self.ix.cmds.RenameItem(str(tx), self.name + suffix)
		return tx

	def update_displacement(self, height):
		"""Updates a Displacement map with new height settings."""
		disp = self.get('displacement_map')
		if disp:
			attrs = self.ix.api.CoreStringArray(5)
			attrs[0] = str(disp) + ".bound[0]"
			attrs[1] = str(disp) + ".bound[1]"
			attrs[2] = str(disp) + ".bound[2]"
			attrs[3] = str(disp) + ".front_value"
			attrs[4] = str(disp) + ".front_offset"
			values = self.ix.api.CoreStringArray(5)
			values[0] = str(height * 1.1)
			values[1] = str(height * 1.1)
			values[2] = str(height * 1.1)
			values[3] = str(height)
			values[4] = str((height / 2) * -1)
			self.ix.cmds.SetValues(attrs, values)
		self.height = height

	def update_opacity(self, clip_opacity, found_textures, update_textures):
		"""Connect/Disconnect the opacity texture depending if clip_opacity is set to False/True."""
		if 'opacity' in update_textures and 'opacity' in found_textures:
			if clip_opacity and self.ix.get_item(str(self.mtl) + '.opacity').get_texture():
				self.ix.cmds.SetTexture([str(self.mtl) + ".opacity"], '')
			elif not clip_opacity and not self.ix.get_item(str(self.mtl) + '.opacity').get_texture():
				self.ix.cmds.SetTexture([str(self.mtl) + ".opacity"], str(self.get('opacity')))

	def update_names(self, name):
		"""Updates all texture names used in the context."""
		ctx = self.ctx
		self.ix.cmds.RenameItem(str(ctx), name)

		objects_array = self.ix.api.OfObjectArray(ctx.get_object_count())
		flags = self.ix.api.CoreBitFieldHelper()
		ctx.get_all_objects(objects_array, flags, False)

		for ctx_member in objects_array:
			self.ix.cmds.RenameItem(str(ctx_member), ctx_member.get_contextual_name().replace(self.name, name))
		self.name = name

	def destroy_tx(self, index):
		"""Removes a texture and its pair."""
		if index == 'displacement':
			self.destroy_tx('displacement_map')
		elif index == 'normal':
			self.destroy_tx('normal_map')
		elif index == 'bump':
			self.destroy_tx('bump_map')
		elif index == 'ior':
			self.destroy_tx('ior_divide')
		# Remove triplanar pair. If texture is triplanar avoid infinite recursion.
		if self.projection == 'triplanar' and not index.endswith('_triplanar'):
			self.destroy_tx(index + "_triplanar")
		self.ix.cmds.DeleteItems([str(self.get(index))])
		self.textures.pop(index, None)

	def get(self, index):
		"""Returns a texture."""
		return self.textures.get(index)

	def clean(self):
		"""Resets the emissive or translucency attributes to 0 when not used."""
		if not self.get('emissive'):
			self.ix.cmds.SetValue(str(self.mtl) + ".emission_strength", [str(0)])
		if not self.get('translucency'):
			self.ix.cmds.SetValue(str(self.mtl) + ".diffuse_back_strength", [str(0)])


def get_json_data_from_directory(directory):
	"""Get the JSON data contents required for material setup."""
	files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
	# Search for any JSON file. Custom Mixer scans don't have a suffix like the ones from the library.
	data = {}
	for f in files:
		filename, extension = os.path.splitext(f)
		if extension == ".json":
			with open(os.path.join(directory, filename + ".json")) as json_file:
				json_data = json.load(json_file)
				if not json_data:
					return None
				meta_data = json_data.get('meta')
				if not meta_data:
					return None
				categories = json_data.get('categories')
				if not categories:
					return None
				if categories:
					if "3d" in categories:
						data['type'] = '3d'
					if "atlas" in categories:
						data['type'] = 'atlas'
					if "3dplant" in categories:
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
	return data


def import_asset(asset_directory, target_ctx=None, ior=DEFAULT_IOR, projection_type="triplanar", object_space=0,
				 clip_opacity=True, srgb=None, triplanar_blend=0.5, **kwargs):
	"""Imports a surface, atlas or object."""
	ix = get_ix(kwargs.get("ix"))
	if not target_ctx:
		target_ctx = ix.application.get_working_context()
	if not check_context(target_ctx, ix=ix):
		return None

	# Initial data
	json_data = get_json_data_from_directory(asset_directory)
	if not json_data:
		ix.log_warning("Could not find a Megascans JSON file. Defaulting to standard settings.")
	asset_type = json_data.get('type', "surface")
	surface_height = json_data.get('surface_height', DEFAULT_DISPLACEMENT_HEIGHT)
	scan_area = json_data.get('scan_area', DEFAULT_UV_SCALE)
	tileable = json_data.get('tileable', True)
	asset_name = os.path.basename(os.path.normpath(asset_directory))

	if asset_type in ["3d", "atlas", "3dplant"]:
		projection_type = 'uv'

	if asset_type == '3dplant':
		# Megascans 3dplant importer. The 3dplant importer requires 2 materials to be created.
		# Let's first find the textures of the Atlas and create the material.
		atlas_textures = get_textures_from_directory(os.path.join(asset_directory, 'Textures/Atlas/'))
		if not atlas_textures:
			ix.log_warning("No textures found in directory.")
			return None

		atlas_surface = Surface(ix, projection='uv', uv_scale=scan_area, height=DEFAULT_PLANT_DISPLACEMENT_HEIGHT,
								tile=tileable, object_space=object_space, triplanar_blend=triplanar_blend, ior=ior)
		plant_root_ctx = ix.cmds.CreateContext(asset_name, "Global", str(target_ctx))
		atlas_mtl = atlas_surface.create_mtl(ATLAS_CTX, plant_root_ctx)
		atlas_surface.create_textures(atlas_textures, srgb, clip_opacity=clip_opacity)
		atlas_ctx = atlas_surface.ctx
		# Find the textures of the Billboard and create the material.
		billboard_textures = get_textures_from_directory(os.path.join(asset_directory, 'Textures/Billboard/'))
		if not billboard_textures:
			ix.log_warning("No textures found in directory.")
			return None

		billboard_surface = Surface(ix, projection='uv', uv_scale=scan_area, height=surface_height,
									tile=tileable, object_space=object_space, triplanar_blend=triplanar_blend, ior=ior)
		billboard_mtl = billboard_surface.create_mtl(BILLBOARD_CTX, plant_root_ctx)
		billboard_surface.create_textures(billboard_textures, srgb, clip_opacity=clip_opacity)
		billboard_ctx = billboard_surface.ctx

		for dir_name in os.listdir(asset_directory):
			variation_dir = os.path.join(asset_directory, dir_name)
			if os.path.isdir(variation_dir) and dir_name.startswith('Var'):
				files = [f for f in os.listdir(variation_dir) if os.path.isfile(os.path.join(variation_dir, f))]
				# Search for models files and apply material
				objs = []
				for f in files:
					filename, extension = os.path.splitext(f)
					if extension == ".obj":
						filename, extension = os.path.splitext(f)
						polyfile = ix.cmds.CreateObject(filename, "GeometryPolyfile", "Global", str(plant_root_ctx))
						ix.cmds.SetValue(str(polyfile) + ".filename", [os.path.join(variation_dir, f)])
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
								if int(lod_level_match) in ATLAS_LOD_DISPLACEMENT_LEVELS:
									geo.assign_displacement(atlas_surface.get('displacement_map').get_module(), i)
					elif extension == ".abc":
						abc_reference = ix.cmds.CreateFileReference(str(plant_root_ctx),
																	[os.path.join(variation_dir, f)])

		shading_layer = ix.cmds.CreateObject(asset_name + SHADING_LAYER_SUFFIX, "ShadingLayer", "Global",
											 str(plant_root_ctx))
		for i in range(0, 4):
			ix.cmds.AddShadingLayerRule(str(shading_layer), i, ["filter", "", "is_visible", "1"])
			ix.cmds.SetShadingLayerRulesProperty(str(shading_layer), [i], "filter", ["./*LOD" + str(i) + "*"])
			ix.cmds.SetShadingLayerRulesProperty(str(shading_layer), [i], "material", [str(atlas_mtl)])
			if atlas_surface.get('opacity') and clip_opacity:
				ix.cmds.SetShadingLayerRulesProperty(str(shading_layer), [i], "clip_map",
													 [str(atlas_surface.get('opacity'))])
			if atlas_surface.get('displacement') and i in ATLAS_LOD_DISPLACEMENT_LEVELS:
				ix.cmds.SetShadingLayerRulesProperty(str(shading_layer), [i], "displacement",
													 [str(atlas_surface.get('displacement_map'))])

			group = ix.cmds.CreateObject(asset_name + "_LOD" + str(i) + GROUP_SUFFIX, "Group", "Global",
										 str(plant_root_ctx))
			group.attrs.inclusion_rule = "./*LOD" + str(i) + "*"
			ix.cmds.AddValues([group.get_full_name() + ".filter"], ["GeometryAbcMesh"])
			ix.cmds.AddValues([group.get_full_name() + ".filter"], ["GeometryPolyfile"])
			ix.cmds.RemoveValue([group.get_full_name() + ".filter"], [2, 0, 1])

	else:
		# All assets except 3dplant have the material in the root directory of the asset.
		textures = get_textures_from_directory(asset_directory)
		if not textures:
			return ix.log_warning("No textures found in directory.")

		surface = Surface(ix, projection=projection_type, uv_scale=scan_area, height=surface_height, tile=tileable,
						  object_space=object_space, triplanar_blend=triplanar_blend, ior=ior)
		mtl = surface.create_mtl(asset_name, target_ctx)
		surface.create_textures(textures, srgb, clip_opacity=clip_opacity)
		ctx = surface.ctx

		if asset_type == '3d':
			# Megascans geometry handling. OBJ files will have materials assigned to them.
			lod_mtls = {}
			if 'normal_lods' in textures and 'normal' in textures:
				normal_lods = {}
				for normal_lod_file in textures['normal_lods']:
					lod_filename, lod_ext = os.path.splitext(normal_lod_file)
					lod_level_match = re.sub('.*?([0-9]*)$', r'\1', lod_filename)
					lod_level = int(lod_level_match)
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
			instance_geo = None
			for f in files:
				filename, extension = os.path.splitext(f)
				if extension == ".obj":
					if "normal_lods" in textures and re.search(r'_LOD[0-9]$', filename, re.IGNORECASE):
						lod_level = re.sub('.*?([0-9]*)$', r'\1', filename)
						# print "Found LOD = " + str(lod_level)
						object_material = lod_mtls[lod_level]
					else:
						object_material = mtl
					# TODO: Instancing doesn't work properly. RenameItem runs asynchronously after assignment causing issues.
					# if instance_geo:
					#     polyfile = ix.cmds.Instantiate([str(instance_geo)])[0]
					#     ix.cmds.LocalizeAttributes([str(polyfile) + ".filename"], True)
					#     ix.cmds.RenameItem(str(polyfile), filename)
					# else:
					# instance_geo = polyfile
					polyfile = ix.cmds.CreateObject(filename, "GeometryPolyfile", "Global", str(ctx))
					ix.cmds.SetValue(str(polyfile) + ".filename", [os.path.join(asset_directory, f)])
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
																[os.path.join(asset_directory, f)])
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
		elif asset_type == "atlas":
			files = [f for f in os.listdir(asset_directory) if os.path.isfile(os.path.join(asset_directory, f))]
			polyfiles = []
			for key, f in enumerate(files):
				filename, extension = os.path.splitext(f)
				if extension == ".obj":
					polyfile = ix.cmds.CreateObject(filename, "GeometryPolyfile", "Global",
													str(ctx))
					polyfile.attrs.filename = os.path.join(asset_directory, f)
					geo = polyfile.get_module()
					for i in range(geo.get_shading_group_count()):
						geo.assign_material(mtl.get_module(), i)
						if textures.get('opacity') and clip_opacity:
							geo.assign_clip_map(surface.get('opacity').get_module(), i)
					polyfiles.append(polyfile)
				elif extension == ".abc":
					abc_reference = ix.cmds.CreateFileReference(str(ctx),
																[os.path.join(asset_directory, f)])
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
			group = ix.cmds.CreateObject("geometry_group", "Group", "Global", str(ctx))
			group.attrs.inclusion_rule = "./*"
			ix.cmds.AddValues([group.get_full_name() + ".filter"], ["GeometryAbcMesh"])
			ix.cmds.AddValues([group.get_full_name() + ".filter"], ["GeometryPolyfile"])
			ix.cmds.RemoveValue([group.get_full_name() + ".filter"], [2, 0, 1])
		return surface


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
	ix = get_ix(kwargs.get("ix"))
	if not check_context(ctx, ix=ix):
		return None
	objects_array = ix.api.OfObjectArray(ctx.get_object_count())
	flags = ix.api.CoreBitFieldHelper()
	ctx.get_all_objects(objects_array, flags, False)
	surface_name = os.path.basename(str(ctx))

	mtl = None
	diffuse_tx = None
	specular_tx = None
	roughness_tx = None
	disp = None
	disp_tx = None
	for ctx_member in objects_array:
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
		ix.log_warning("No MaterialPhysicalStandard found in context.")
		return False
	if not disp and not disp_tx and displacement_blend:
		ix.log_warning("No Displacement found in context. Cannot use Displacement blending.")
		return False
	elif not diffuse_tx or not specular_tx or not roughness_tx:
		ix.log_warning("Make sure the material has a diffuse, specular and roughness texture.")
		return False

	multi_blend_tx = ix.cmds.CreateObject(surface_name + MOISTURE_SUFFIX + MULTI_BLEND_SUFFIX, "TextureMultiBlend",
										  "Global", str(ctx))
	# Setup fractal noise
	fractal_selector = create_fractal_selector(ctx, surface_name, MOISTURE_SUFFIX, ix=ix)

	# Setup slope gradient
	slope_selector = create_slope_selector(ctx, surface_name, MOISTURE_SUFFIX, ix=ix)

	# Setup scope
	scope_selector = create_scope_selector(ctx, surface_name, MOISTURE_SUFFIX, ix=ix)

	# Setup triplanar
	triplanar_selector = create_triplanar_selector(ctx, surface_name, MOISTURE_SUFFIX, ix=ix)

	# Setup AO
	ao_selector = create_ao_selector(ctx, surface_name, MOISTURE_SUFFIX, ix=ix)

	# Setup height blend
	height_selector = create_height_selector(ctx, surface_name, MOISTURE_SUFFIX, ix=ix, invert=True)

	disp_selector = None
	# Setup displacement blend
	if disp and disp_tx:
		disp_selector = create_displacement_selector(disp_tx, ctx, surface_name, "_moisture", ix=ix)

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
	diffuse_blend_tx = ix.cmds.CreateObject(surface_name + MOISTURE_DIFFUSE_BLEND_SUFFIX, "TextureBlend", "Global",
											str(ctx))
	diffuse_blend_tx.attrs.input1[0] = diffuse_multiplier
	diffuse_blend_tx.attrs.input1[1] = diffuse_multiplier
	diffuse_blend_tx.attrs.input1[2] = diffuse_multiplier
	diffuse_blend_tx.attrs.mode = 7
	ix.cmds.SetTexture([str(diffuse_blend_tx) + ".mix"], str(multi_blend_tx))

	connected_attrs = ix.api.OfAttrVector()
	get_attrs_connected_to_texture(diffuse_tx, connected_attrs, ix=ix)
	for i_attr in range(0, connected_attrs.get_count()):
		ix.cmds.SetTexture([str(connected_attrs[i_attr])], str(diffuse_blend_tx))
	ix.cmds.SetTexture([str(diffuse_blend_tx) + ".input2"], str(diffuse_tx))

	# Setup specular blend
	specular_blend_tx = ix.cmds.CreateObject(surface_name + MOISTURE_SPECULAR_BLEND_SUFFIX, "TextureBlend", "Global",
											 str(ctx))
	ix.cmds.SetTexture([str(specular_blend_tx) + ".mix"], str(multi_blend_tx))
	specular_blend_tx.attrs.input1[0] = specular_multiplier
	specular_blend_tx.attrs.input1[1] = specular_multiplier
	specular_blend_tx.attrs.input1[2] = specular_multiplier
	specular_blend_tx.attrs.mode = 8

	connected_attrs = ix.api.OfAttrVector()
	get_attrs_connected_to_texture(specular_tx, connected_attrs, ix=ix)
	for i_attr in range(0, connected_attrs.get_count()):
		ix.cmds.SetTexture([str(connected_attrs[i_attr])], str(specular_blend_tx))
	ix.cmds.SetTexture([str(specular_blend_tx) + ".input2"], str(specular_tx))

	# Setup roughness blend
	roughness_blend_tx = ix.cmds.CreateObject(surface_name + MOISTURE_ROUGHNESS_BLEND_SUFFIX, "TextureBlend", "Global",
											  str(ctx))
	ix.cmds.SetTexture([str(roughness_blend_tx) + ".mix"], str(multi_blend_tx))
	roughness_blend_tx.attrs.input1[0] = roughness_multiplier
	roughness_blend_tx.attrs.input1[1] = roughness_multiplier
	roughness_blend_tx.attrs.input1[2] = roughness_multiplier
	roughness_blend_tx.attrs.mode = 7

	connected_attrs = ix.api.OfAttrVector()
	get_attrs_connected_to_texture(roughness_tx, connected_attrs, ix=ix)
	for i_attr in range(0, connected_attrs.get_count()):
		ix.cmds.SetTexture([str(connected_attrs[i_attr])], str(roughness_blend_tx))
	ix.cmds.SetTexture([str(roughness_blend_tx) + ".input2"], str(roughness_tx))

	# Setup IOR blend
	ior_tx = ix.cmds.CreateObject(surface_name + MOISTURE_IOR_BLEND_SUFFIX, "TextureBlend", "Global", str(ctx))
	ior_tx.attrs.input2[0] = DEFAULT_IOR
	ior_tx.attrs.input2[1] = DEFAULT_IOR
	ior_tx.attrs.input2[2] = DEFAULT_IOR
	ior_tx.attrs.input1[0] = ior
	ior_tx.attrs.input1[1] = ior
	ior_tx.attrs.input1[2] = ior
	ix.cmds.SetTexture([str(ior_tx) + ".mix"], str(multi_blend_tx))

	ix.cmds.SetTexture([str(mtl) + ".specular_1_index_of_refraction"], str(ior_tx))


def tint_surface(ctx, color, strength=.5, **kwargs):
	"""
	Tints the diffuse texture with the specified color
	"""
	ix = get_ix(kwargs.get("ix"))
	if not check_context(ctx, ix=ix):
		return None

	objects_array = ix.api.OfObjectArray(ctx.get_object_count())
	flags = ix.api.CoreBitFieldHelper()
	ctx.get_all_objects(objects_array, flags, False)
	surface_name = os.path.basename(str(ctx))
	mtl = None
	for ctx_member in objects_array:
		if check_selection([ctx_member], is_kindof=["MaterialPhysicalStandard", ], max_num=1):
			if ctx_member.is_local() or not mtl:
				mtl = ctx_member
	if not mtl:
		ix.log_warning("No valid material or displacement found.")
		return False

	diffuse_tx = ix.get_item(str(mtl) + '.diffuse_front_color').get_texture()
	tint_tx = ix.cmds.CreateObject(surface_name + DIFFUSE_TINT_SUFFIX, "TextureBlend", "Global", str(ctx))
	tint_tx.attrs.mix = strength
	tint_tx.attrs.mode = 12
	tint_tx.attrs.input1[0] = color[0]
	tint_tx.attrs.input1[1] = color[1]
	tint_tx.attrs.input1[2] = color[2]
	ix.cmds.SetTexture([str(tint_tx) + ".input2"], str(diffuse_tx))
	ix.cmds.SetTexture([str(mtl) + ".diffuse_front_color"], str(tint_tx))
	return tint_tx


def replace_surface(ctx, surface_directory, ior=DEFAULT_IOR, projection_type="triplanar", object_space=0,
					clip_opacity=True, srgb=(), triplanar_blend=0.5, **kwargs):
	"""
	Replace the selected surface context with a different surface.
	Links between blend materials are maintained.
	"""
	ix = get_ix(kwargs.get("ix"))
	if not check_context(ctx, ix=ix):
		return None
	# Initial data

	json_data = get_json_data_from_directory(surface_directory)
	if not json_data:
		ix.log_warning("Could not find a Megascans JSON file. Defaulting to standard settings.")
	surface_height = json_data.get('surface_height', DEFAULT_DISPLACEMENT_HEIGHT)
	scan_area = json_data.get('scan_area', DEFAULT_UV_SCALE)
	tileable = json_data.get('tileable', True)
	surface_name = os.path.basename(os.path.normpath(surface_directory))

	# Let's find the textures
	textures = get_textures_from_directory(surface_directory)
	if not textures:
		ix.log_warning("No textures found in directory.")
		return False

	surface = Surface(ix)
	surface.load(ctx)
	update_textures = {}
	for key, tx in surface.textures.copy().iteritems():
		if tx.is_kindof("TextureMapFile"):
			# Swap filename
			if key in textures:
				print "UPDATING FROM SURFACE: " + key
				update_textures[key] = textures.get(key)
			elif key not in textures:
				print "DELETING FROM SURFACE: " + key
				surface.destroy_tx(key)
	new_textures = {}
	for key, tx in textures.iteritems():
		if key not in surface.textures:
			if (key == 'gloss' and 'roughness' in surface.textures) or \
					(key == 'roughness' and 'gloss' in surface.textures):
				continue
			if (key == 'normal' and 'bump' in surface.textures) or \
					(key == 'bump' and 'normal' in surface.textures):
				continue
			print "NOT IN SURFACE: " + key
			new_textures[key] = tx

	surface.create_textures(new_textures, srgb=srgb, clip_opacity=clip_opacity)
	surface.update_ior(ior)
	surface.update_projection(projection=projection_type, uv_scale=scan_area,
							  triplanar_blend=triplanar_blend, object_space=object_space, tile=True)
	surface.update_textures(update_textures, srgb)
	surface.update_names(surface_name)
	surface.update_displacement(surface_height)
	surface.update_opacity(clip_opacity=clip_opacity, found_textures=textures, update_textures=update_textures)
	surface.clean()
	return surface


def mix_surfaces(ctx1, ctx2, mix_surface_name="mix" + MATERIAL_SUFFIX,
				 target_context=None, displacement_blend=True, height_blend=False,
				 ao_blend=False, fractal_blend=True, triplanar_blend=True,
				 slope_blend=True, scope_blend=True, **kwargs):
	"""Mixes 2 surfaces with each other."""
	ix = get_ix(kwargs.get("ix"))
	if not target_context:
		target_context = ix.application.get_working_context()
	if not check_context(target_context, ix=ix):
		return None
	print "Mixing surfaces"
	mtl1 = get_mtl_from_context(ctx1, ix=ix)
	disp1 = get_disp_from_context(ctx1, ix=ix)
	mtl2 = get_mtl_from_context(ctx2, ix=ix)
	disp2 = get_disp_from_context(ctx2, ix=ix)
	has_displacement = disp1 and disp2
	surface1_name = ctx1.get_name()
	surface2_name = ctx2.get_name()

	ctx = ix.cmds.CreateContext(mix_surface_name, "Global", str(target_context))

	disp1_offset_tx = None
	disp2_offset_tx = None
	disp_branch_selector = None

	if has_displacement:
		# Setup displacements for height blending.
		# Surface 1
		print "Setting up surface 1"
		surface1_height = disp1.attrs.front_value[0]
		print "Surface 1 height: " + str(surface1_height)
		disp1_tx_front_value = ix.get_item(str(disp1) + ".front_value")
		disp1_tx = disp1_tx_front_value.get_texture()
		disp1_height_scale_tx = ix.cmds.CreateObject(surface1_name + DISPLACEMENT_HEIGHT_SCALE_SUFFIX,
													 "TextureMultiply", "Global", str(ctx))
		ix.cmds.SetTexture([str(disp1_height_scale_tx) + ".input1"], str(disp1_tx))

		disp1_height_scale_tx.attrs.input2[0] = surface1_height
		disp1_height_scale_tx.attrs.input2[1] = surface1_height
		disp1_height_scale_tx.attrs.input2[2] = surface1_height
		disp1_blend_offset_tx = ix.cmds.CreateObject(surface1_name + DISPLACEMENT_BLEND_OFFSET_SUFFIX,
													 "TextureAdd", "Global", str(ctx))
		ix.cmds.SetTexture([str(disp1_blend_offset_tx) + ".input1"], str(disp1_height_scale_tx))
		disp1_offset_tx = ix.cmds.CreateObject(surface1_name + DISPLACEMENT_OFFSET_SUFFIX, "TextureAdd",
											   "Global", str(ctx))
		disp1_offset_tx.attrs.input2[0] = (surface1_height / 2) * -1
		disp1_offset_tx.attrs.input2[1] = (surface1_height / 2) * -1
		disp1_offset_tx.attrs.input2[2] = (surface1_height / 2) * -1
		ix.cmds.SetTexture([str(disp1_offset_tx) + ".input1"], str(disp1_height_scale_tx))

		# Surface 2
		print "Setting up surface 2"
		surface2_height = disp2.attrs.front_value[0]
		print "Surface 2 height: " + str(surface2_height)
		disp2_tx_front_value = ix.get_item(str(disp2) + ".front_value")
		disp2_tx = disp2_tx_front_value.get_texture()
		disp2_height_scale_tx = ix.cmds.CreateObject(surface2_name + DISPLACEMENT_HEIGHT_SCALE_SUFFIX,
													 "TextureMultiply", "Global", str(ctx))
		ix.cmds.SetTexture([str(disp2_height_scale_tx) + ".input1"], str(disp2_tx))
		disp2_height_scale_tx.attrs.input2[0] = surface2_height
		disp2_height_scale_tx.attrs.input2[1] = surface2_height
		disp2_height_scale_tx.attrs.input2[2] = surface2_height
		disp2_blend_offset_tx = ix.cmds.CreateObject(surface2_name + DISPLACEMENT_BLEND_OFFSET_SUFFIX,
													 "TextureAdd", "Global", str(ctx))
		ix.cmds.SetTexture([str(disp2_blend_offset_tx) + ".input1"], str(disp2_height_scale_tx))
		disp2_offset_tx = ix.cmds.CreateObject(surface2_name + DISPLACEMENT_OFFSET_SUFFIX, "TextureAdd",
											   "Global", str(ctx))
		disp2_offset_tx.attrs.input2[0] = (surface1_height / 2) * -1
		disp2_offset_tx.attrs.input2[1] = (surface1_height / 2) * -1
		disp2_offset_tx.attrs.input2[2] = (surface1_height / 2) * -1
		ix.cmds.SetTexture([str(disp2_offset_tx) + ".input1"], str(disp2_height_scale_tx))

		disp_branch_selector = ix.cmds.CreateObject(mix_surface_name + DISPLACEMENT_BRANCH_SUFFIX, "TextureBranch",
													"Global",
													str(ctx))

		ix.cmds.SetTexture([str(disp_branch_selector) + ".input_a"], str(disp1_blend_offset_tx))
		ix.cmds.SetTexture([str(disp_branch_selector) + ".input_b"], str(disp2_blend_offset_tx))
		disp_branch_selector.attrs.mode = 2

	# Setup fractal noise
	fractal_selector = create_fractal_selector(ctx, mix_surface_name, "_mix", ix=ix)

	# Setup slope gradient
	slope_selector = create_slope_selector(ctx, mix_surface_name, "_mix", ix=ix)

	# Setup scope
	scope_selector = create_scope_selector(ctx, mix_surface_name, "_mix", ix=ix)

	# Setup triplanar
	triplanar_selector = create_triplanar_selector(ctx, mix_surface_name, "_mix", ix=ix)

	# Setup AO
	ao_selector = create_ao_selector(ctx, mix_surface_name, "_mix", ix=ix)

	# Setup height blend
	height_selector = create_height_selector(ctx, mix_surface_name, "_mix", ix=ix)

	# Put all selectors in a TextureMultiBlend
	multi_blend_tx = ix.cmds.CreateObject(mix_surface_name + MULTI_BLEND_SUFFIX, "TextureMultiBlend",
										  "Global", str(ctx))
	multi_blend_tx.attrs.layer_1_label[0] = "Base intensity"
	# Attach Ambient Occlusion blend
	multi_blend_tx.attrs.enable_layer_2 = True
	multi_blend_tx.attrs.layer_2_mode = 1
	multi_blend_tx.attrs.layer_2_label[0] = "Ambient Occlusion Blend"
	ix.cmds.SetTexture([str(multi_blend_tx) + ".layer_2_color"], str(ao_selector))
	if not ao_blend: multi_blend_tx.attrs.enable_layer_2 = False
	# Attach displacement blend
	multi_blend_tx.attrs.enable_layer_3 = True
	multi_blend_tx.attrs.layer_3_label[0] = "Displacement Blend"
	multi_blend_tx.attrs.layer_3_mode = 1
	if disp_branch_selector:
		ix.cmds.SetTexture([str(multi_blend_tx) + ".layer_3_color"], str(disp_branch_selector))
		if not displacement_blend: multi_blend_tx.attrs.enable_layer_3 = False
		# Finalize new Displacement map
		disp_multi_blend_tx = ix.cmds.CreateObject(mix_surface_name + DISPLACEMENT_BLEND_SUFFIX, "TextureMultiBlend",
												   "Global", str(ctx))
		ix.cmds.SetTexture([str(disp_multi_blend_tx) + ".layer_1_color"], str(disp1_offset_tx))
		disp_multi_blend_tx.attrs.enable_layer_2 = True
		disp_multi_blend_tx.attrs.layer_2_label[0] = "Mix mode"
		ix.cmds.SetTexture([str(disp_multi_blend_tx) + ".layer_2_color"], str(disp2_offset_tx))
		ix.cmds.SetTexture([str(disp_multi_blend_tx) + ".layer_2_mix"], str(multi_blend_tx))
		disp_multi_blend_tx.attrs.enable_layer_3 = True
		disp_multi_blend_tx.attrs.layer_3_label[0] = "Add mode"
		ix.cmds.SetTexture([str(disp_multi_blend_tx) + ".layer_3_color"], str(disp2_offset_tx))
		ix.cmds.SetTexture([str(disp_multi_blend_tx) + ".layer_3_mix"], str(multi_blend_tx))
		disp_multi_blend_tx.attrs.layer_3_mode = 6
		disp_multi_blend_tx.attrs.enable_layer_3 = False

		displacement_map = ix.cmds.CreateObject(mix_surface_name + DISPLACEMENT_MAP_SUFFIX, "Displacement", "Global",
												str(ctx))
		displacement_map.attrs.bound[0] = 1
		displacement_map.attrs.bound[1] = 1
		displacement_map.attrs.bound[2] = 1
		displacement_map.attrs.front_value = 1
		ix.cmds.SetTexture([str(displacement_map) + ".front_value"], str(disp_multi_blend_tx))
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

	# Blend materials
	blend_mtl = ix.cmds.CreateObject(mix_surface_name + MATERIAL_SUFFIX, "MaterialPhysicalBlend", "Global", str(ctx))
	ix.cmds.SetTexture([str(blend_mtl) + ".mix"], str(multi_blend_tx))
	ix.cmds.SetValue(str(blend_mtl) + ".input2", [str(mtl1)])
	ix.cmds.SetValue(str(blend_mtl) + ".input1", [str(mtl2)])
	return blend_mtl


def toggle_surface_complexity(ctx, **kwargs):
	"""Temporarily replaces the current surface with a much simpeler MaterialPhysicalDiffuse material."""
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
		diffuse_tx = ix.get_item(str(mtl) + '.diffuse_front_color').get_texture()
		new_preview_mtl = ix.cmds.CreateObject(surface_name + PREVIEW_MATERIAL_SUFFIX, "MaterialPhysicalDiffuse",
											   "Global", str(ctx))
		ix.cmds.SetTexture([new_preview_mtl.get_full_name() + ".front_color"],
						   str(diffuse_tx))
		connected_attrs = ix.api.OfAttrVector()
		get_attrs_connected_to_texture(mtl, connected_attrs, ix=ix)
		for i in range(0, connected_attrs.get_count()):
			print connected_attrs[i]
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
		connected_attrs = ix.api.OfAttrVector()
		get_attrs_connected_to_texture(preview_mtl, connected_attrs, ix=ix)
		for i in range(0, connected_attrs.get_count()):
			print connected_attrs[i]
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


def tx_to_triplanar(tx, blend=0.5, object_space=0, **kwargs):
	"""Converts the texture to triplanar."""
	ix = get_ix(kwargs.get("ix"))
	print "Triplanar Blend: " + str(blend)
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
	"""Moistens the selected material."""
	ix = get_ix(kwargs.get("ix"))
	if not ctx:
		ctx = ix.application.get_working_context()
	if not check_context(ctx, ix=ix):
		return None

	geo_name = geometry.get_contextual_name()
	pc = ix.cmds.CreateObject(geo_name + POINTCLOUD_SUFFIX, pc_type, "Global", str(ctx))
	if pc_type == "GeometryPointCloud":
		if use_density:
			pc.attrs.use_density = True
			pc.attrs.density = density
		else:
			pc.attrs.point_count = int(point_count)
	else:
		pc.attrs.point_count = int(point_count)

	multi_blend_tx = ix.cmds.CreateObject(geo_name + DECIMATE_SUFFIX + MULTI_BLEND_SUFFIX, "TextureMultiBlend",
										  "Global", str(ctx))
	# Setup fractal noise
	fractal_selector = create_fractal_selector(ctx, geo_name, DECIMATE_SUFFIX, ix=ix)

	# Setup slope gradient
	slope_selector = create_slope_selector(ctx, geo_name, DECIMATE_SUFFIX, ix=ix)

	# Setup scope
	scope_selector = create_scope_selector(ctx, geo_name, DECIMATE_SUFFIX, ix=ix)

	# Setup triplanar
	triplanar_selector = create_triplanar_selector(ctx, geo_name, DECIMATE_SUFFIX, ix=ix)

	# Setup AO
	ao_selector = create_ao_selector(ctx, geo_name, DECIMATE_SUFFIX, ix=ix)

	# Setup height blend
	height_selector = create_height_selector(ctx, geo_name, DECIMATE_SUFFIX, ix=ix)

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
		# Refresh bug!

	ix.cmds.SetValue(str(pc) + ".geometry", [str(geometry)])
	return pc


def import_ms_library(library_dir, target_ctx=None, custom_assets=True, skip_categories=(), **kwargs):
	"""Imports the whole Megascans Library. Point it to the Downloaded folder inside your library folder.
	"""
	ix = get_ix(kwargs.get("ix"))
	if not target_ctx:
		target_ctx = ix.application.get_working_context()
	if not check_context(target_ctx, ix=ix):
		return None
	if os.path.isdir(os.path.join(library_dir, "Downloaded")):
		library_dir = os.path.join(library_dir, "Downloaded")

	print "Scanning folders in " + library_dir

	for category_dir_name in os.listdir(library_dir):
		category_dir_path = os.path.join(library_dir, category_dir_name)
		if category_dir_name in ["3d", "3dplant", "surface", "surfaces", "atlas"]:
			if category_dir_name not in skip_categories and os.path.isdir(category_dir_path):
				context_name = category_dir_name
				if category_dir_name == "surfaces":
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
							import_asset(asset_directory_path, target_ctx=ctx, srgb=MEGASCANS_SRGB_TEXTURES, ix=ix)
	if custom_assets:
		import_ms_library(os.path.join(library_dir, "My Assets"), target_ctx=target_ctx,
						  skip_categories=skip_categories, custom_assets=False, ix=ix)
