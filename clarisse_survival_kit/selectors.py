from clarisse_survival_kit.settings import *
from clarisse_survival_kit.utility import add_gradient_key
import random


def create_height_selector(ctx, name, name_suffix, ix, invert=False):
	world_position_tx = ix.cmds.CreateObject(name + name_suffix + WORLD_POSITION_SUFFIX, "TextureUtility", "Global",
											 str(ctx))
	world_position_reorder_tx = ix.cmds.CreateObject(name + name_suffix + WORLD_POSITION_REORDER_SUFFIX,
													 "TextureReorder", "Global", str(ctx))
	world_position_reorder_tx.attrs.channel_order[0] = "ggga"
	ix.cmds.SetTexture([str(world_position_reorder_tx) + ".input"], str(world_position_tx))

	height_gradient_tx = ix.cmds.CreateObject(name + name_suffix + HEIGHT_GRADIENT_SUFFIX, "TextureGradient", "Global",
											  str(ctx))
	if invert:
		add_gradient_key(str(height_gradient_tx) + ".output", 0.45, [1, 1, 1], ix=ix)
		add_gradient_key(str(height_gradient_tx) + ".output", 0.55, [0, 0, 0], ix=ix)
	else:
		add_gradient_key(str(height_gradient_tx) + ".output", 0.45, [0, 0, 0], ix=ix)
		add_gradient_key(str(height_gradient_tx) + ".output", 0.55, [1, 1, 1], ix=ix)
	ix.cmds.RemoveCurveValue([str(height_gradient_tx) + ".output"], [1, 1, 1, 1, 1, 1, 1, 1])
	ix.cmds.SetTexture([str(height_gradient_tx) + ".input"], str(world_position_reorder_tx))
	return height_gradient_tx


def create_displacement_selector(disp_tx, ctx, name, name_suffix, ix):
	branch_tx = ix.cmds.CreateObject(name + name_suffix + DISPLACEMENT_BRANCH_SUFFIX, "TextureBranch", "Global",
									 str(ctx))
	offset_tx = ix.cmds.CreateObject(name + name_suffix + DISPLACEMENT_OFFSET_SUFFIX, "TextureConstantColor",
									 "Global",
									 str(ctx))
	offset_tx.attrs.color[0] = 0.5
	offset_tx.attrs.color[1] = 0.5
	offset_tx.attrs.color[2] = 0.5

	ix.cmds.SetTexture([str(branch_tx) + ".input_a"], str(disp_tx))
	ix.cmds.SetTexture([str(branch_tx) + ".input_b"], str(offset_tx))
	branch_tx.attrs.mode = 2
	return branch_tx


def create_slope_selector(ctx, name, name_suffix, ix, invert=False):
	# Setup slope gradient
	slope_tx = ix.cmds.CreateObject(name + name_suffix + SLOPE_BLEND_SUFFIX, "TextureGradient", "Global", str(ctx))
	slope_start_color = 0
	slope_end_color = 1
	if invert:
		slope_start_color = 1
		slope_end_color = 0
	add_gradient_key(str(slope_tx) + ".output", 0.80, [slope_start_color, slope_start_color, slope_start_color], ix=ix)
	add_gradient_key(str(slope_tx) + ".output", 0.85, [slope_end_color, slope_end_color, slope_end_color], ix=ix)
	ix.cmds.RemoveCurveValue([str(slope_tx) + ".output"], [1, 1, 1, 1, 1, 1, 1, 1])
	slope_tx.attrs.mode = 2
	return slope_tx


def create_scope_selector(ctx, name, name_suffix, ix):
	# Setup scope
	scope_tx = ix.cmds.CreateObject(name + name_suffix + SCOPE_BLEND_SUFFIX, "TextureScope", "Global", str(ctx))
	scope_obj = ix.cmds.CreateObject(name + name_suffix + SCOPE_OBJ_BLEND_SUFFIX, "Scope", "Global", str(ctx))
	ix.cmds.AddValues([str(scope_tx) + ".scopes"], [str(scope_obj)])
	return scope_tx


def create_ao_selector(ctx, name, name_suffix, ix):
	ao_tx = ix.cmds.CreateObject(name + name_suffix + AO_BLEND_SUFFIX, "TextureOcclusion", "Global", str(ctx))
	ao_tx.attrs.color[0] = 0.0
	ao_tx.attrs.color[1] = 0.0
	ao_tx.attrs.color[2] = 0.0
	ao_tx.attrs.occlusion_color[0] = 1.0
	ao_tx.attrs.occlusion_color[1] = 1.0
	ao_tx.attrs.occlusion_color[2] = 1.0
	ao_tx.attrs.quality = 10
	ao_remap_tx = ix.cmds.CreateObject(name + name_suffix + AO_BLEND_REMAP_SUFFIX, "TextureRemap", "Global", str(ctx))
	ix.cmds.SetTexture([str(ao_remap_tx) + ".input"], str(ao_tx))
	return ao_remap_tx


def create_triplanar_selector(ctx, name, name_suffix, ix, invert=False, blend_ratio=0.5):
	triplanar_tx = ix.cmds.CreateObject(name + name_suffix + TRIPLANAR_BLEND_SUFFIX, "TextureTriplanar",
										"Global", str(ctx))
	start_color = str(0)
	end_color = str(1)
	if invert:
		start_color = str(1)
		end_color = str(0)
	ix.cmds.SetValues([str(triplanar_tx) + ".right"], [start_color, start_color, start_color])
	ix.cmds.SetValues([str(triplanar_tx) + ".left"], [start_color, start_color, start_color])
	ix.cmds.SetValues([str(triplanar_tx) + ".top"], [end_color, end_color, end_color])
	ix.cmds.SetValues([str(triplanar_tx) + ".bottom"], [start_color, start_color, start_color])
	ix.cmds.SetValues([str(triplanar_tx) + ".front"], [start_color, start_color, start_color])
	ix.cmds.SetValues([str(triplanar_tx) + ".back"], [start_color, start_color, start_color])
	triplanar_tx.attrs.object_space = 2
	triplanar_tx.attrs.blend = blend_ratio
	return triplanar_tx


def create_fractal_selector(ctx, name, name_suffix, ix):
	# Setup fractal noise
	fractal_tx = ix.cmds.CreateObject(name + name_suffix + FRACTAL_BLEND_SUFFIX, "TextureFractalNoise", "Global",
									  str(ctx))
	fractal_tx.attrs.color1[0] = 1.0
	fractal_tx.attrs.color1[1] = 1.0
	fractal_tx.attrs.color1[2] = 1.0
	fractal_tx.attrs.contrast = .5
	fractal_tx.attrs.projection = 0
	fractal_tx.attrs.axis = 1
	random_offset = random.randrange(-123456, 123456)
	fractal_tx.attrs.uv_translate[0] = random_offset
	fractal_tx.attrs.uv_translate[1] = random_offset
	fractal_tx.attrs.uv_translate[2] = random_offset

	fractal_tx.attrs.uv_scale[0] = .5
	fractal_tx.attrs.uv_scale[1] = .5
	fractal_tx.attrs.uv_scale[2] = .5
	# Let's balance the noise a bit
	fractal_tx.attrs.turbulent = False
	fractal_tx.attrs.normalize = False
	fractal_clamp_tx = ix.cmds.CreateObject(name + name_suffix + FRACTAL_BLEND_CLAMP_SUFFIX, "TextureClamp", "Global",
											str(ctx))
	ix.cmds.SetTexture([str(fractal_clamp_tx) + ".input"], str(fractal_tx))
	fractal_remap_tx = ix.cmds.CreateObject(name + name_suffix + FRACTAL_BLEND_REMAP_SUFFIX, "TextureRemap", "Global",
											str(ctx))
	ix.cmds.SetTexture([str(fractal_remap_tx) + ".input"], str(fractal_clamp_tx))
	return fractal_remap_tx
