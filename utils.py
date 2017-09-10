import os

# return a list with unique and sorted set of keys of dictionary d1 and d2
def merge_keys_to_list(d1, d2):
	ret = list(set(list(d1.keys()) + list(d2.keys())))	
	ret.sort()
	return ret

def get_output_filename(dirname):
	return os.path.join(dirname, "output")
