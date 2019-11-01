# TODO: remove this file. nothing here is being used


import yaml


def join(loader, node):
	"""Define custom tag handler."""
    seq = loader.construct_sequence(node)
    return ''.join(map(str, seq))

def None_def(loader, node):
	"""Define custom tag handler."""
    return None

def load_config(yml_file):
	"""
	Parameters
	----------
	yml_file : str
		path to yml_file
	key : str
		section within config.yml file to return

	Returns
	-------
	dict object with key 'default' mapping to a dictionary
	of all attributes specified in configs/config.yml.
	Types are specified according to python syntax in yml.
	
	"""	

	# Required for safe_load, register the tag handler
	yaml.SafeLoader.add_constructor('!join', join)
	yaml.SafeLoader.add_constructor('!None', None_def)
	with open(yml_file, 'r') as yml_file:
		return yaml.safe_load(yml_file)
