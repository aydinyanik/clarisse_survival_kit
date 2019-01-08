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