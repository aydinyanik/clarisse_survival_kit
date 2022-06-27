aces_installed = False

for name in ix.api.ColorIO.get_color_space_names():
    if 'Utility - Linear - sRGB' in name:
        aces_installed = True

textures = ix.api.OfObjectVector()
filter = "*"
types = ix.api.CoreStringVector()
types.add('TextureMapFile')
types.add('TextureStreamedMapFile')
ix.application.get_matching_objects(textures, filter, ix.application.get_factory().get_project(), types)

ix.begin_command_batch("ACES Switch")
count = textures.get_count()
ix.log_info(str(count) + " textures found in scene. Checking for unassigned color_spaces...")
progress_msg = 'Switching textures to ACES color spaces...' if aces_installed else 'Switching textures to Clarisse default color spaces...'
ix.log_info(progress_msg)
progress = ix.application.create_progress_bar(progress_msg)
progress.set_value(0.0)
progress.set_step_count(count)
progress.start()

step = 0
changed = 0
for tx in textures:
    if tx.attrs.use_raw_data.attr.get_bool():
        # No need to change raw to Utility - Raw
        pass
    else:
        color_space = tx.attrs.file_color_space.attr.get_string()
        if tx.attrs.color_space_auto_detect.attr.get_bool():
            ix.cmds.SetValues([str(tx) + '.color_space_auto_detect'], ["0"])
            ix.application.check_for_events()
        if aces_installed:
            if 'linear' in color_space.lower():
                ix.cmds.SetValues([str(tx) + '.file_color_space'], ["Utility|Utility - Linear - sRGB"])
                changed += 1
            elif 'srgb' in color_space.lower():
                ix.cmds.SetValues([str(tx) + '.file_color_space'], ["Utility|Utility - sRGB - Texture"])
                changed += 1
        else:
            if color_space == 'Utility|Utility - Linear - sRGB':
                ix.cmds.SetValues([str(tx) + '.file_color_space'], ["linear"])
                changed += 1
            elif color_space == 'Utility|Utility - sRGB - Texture':
                ix.cmds.SetValues([str(tx) + '.file_color_space'], ["Clarisse|sRGB"])
                changed += 1
            elif color_space == 'Utility|Utility - Raw':
                ix.cmds.SetValues([str(tx) + '.use_raw_data'], ["1"])
                changed += 1
    progress.step(step)
    step += step

ix.end_command_batch()
ix.log_info("...done running over all textures. Switched {} textures to other color spaces.".format(str(changed)))