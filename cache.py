import json 

def cache_load(fn):
	try:
		with open(fn, "r") as fd:
			data = json.load(fd)
	except FileNotFoundError:
		return []
	return data

def cache_save(data, fn):
	with open(fn, "w+") as fd:
		json.dump(data, fd)
