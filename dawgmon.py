#!/usr/bin/env python3

import sys, os, tempfile, functools
from datetime import datetime
from argparse import ArgumentParser

import commands
from utils import merge_keys_to_list
from cache import Cache
from local import local_run
from version import VERSION

def compare_output(old, new, commandlist=None):
	anomalies = []
	if not old:
		# if None is passed in it's simply empty
		old = {}
	tasks = merge_keys_to_list(old, new)
	for task_name in tasks:
		cmd = commands.COMMAND_CACHE.get(task_name, None)
		if not cmd:
			print("unknown task_name specified")
			continue
		if commandlist and task_name not in commandlist:
			continue
	
		old_data = old[task_name] if task_name in old else ""
		old_data = cmd.parse(old_data)
		new_data = cmd.parse(new[task_name])
		ret = cmd.compare(old_data, new_data)
		if type(ret) != list:
			raise Exception("unexpected return value type for %s" % cmd)
		if ret and len(ret) > 0:
			anomalies = anomalies + ret
	return anomalies

def print_anomalies(anomalies, show_debug=False, show_color=True):
	changes = list(filter(lambda x:x[0] == commands.CHANGE, anomalies))
	warning = list(filter(lambda x:x[0] == commands.WARNING, anomalies))
	debug = list(filter(lambda x:x[0] == commands.DEBUG, anomalies)) if show_debug else []
	c1 = "\x1b[32m" if show_color else ""
	c2 = "\x1b[31m" if show_color else ""
	c3 = "\x1b[36m" if show_color else ""
	c4 = "\x1b[34m" if show_color else ""
	c_end = "\x1b[0m" if show_color else ""
	la, lw, ld = len(changes), len(warning), len(debug)
	debugs = " and %i debug message%s" % (ld, "s" if ld != 1 else "") if ld > 0 else ""
	print("%s%i change%s detected (%i warning%s%s)%s" % (c1, la, "s" if la != 1 else "", lw, "s" if lw != 1 else "", debugs, c_end))
	for w in warning:
		print("%s! %s%s" % (c2, w[1], c_end))
	for c in changes:
		print("%s+ %s%s" % (c3, c[1], c_end))
	if show_debug:
		for d in debug:
			print("%s- %s%s" % (c4, d[1], c_end))

def run(tmpdirname):

	default_max_cache_entries = 16
	default_cache_name = ".dawgmon.db"

	# parsing and checking arguments
	parser = ArgumentParser(description="attack surface analyzer and change monitor")
	parser.add_argument("-v", "--version", action="version", version=VERSION)
	parser.add_argument("-L", help="list cache entries", dest="list_cache", action="store_true", default=False)
	parser.add_argument("-c", help="location of cache (default: $HOME/%s)" % (default_cache_name), dest="cache_location", metavar="filename", default=None, required=False)
	parser.add_argument("-e", help="execute specific command", dest="commandlist", metavar="command", type=str, action="append")
	parser.add_argument("-d", help="show debug output", dest="show_debug", action="store_true", default=False)
	parser.add_argument("-m", help="max amount of cache entries per host (default: %i)" % default_max_cache_entries,
		dest="max_cache_entries", type=int, metavar="N", default=default_max_cache_entries, required=False)
	args = parser.parse_args()

	if args.max_cache_entries < 1 or args.max_cache_entries > 1024:
		print("maximum number of cache entries invalid or set too high [1-1024]")
		sys.exit(1)

	if not args.cache_location:
		args.cache_location = os.path.join(os.getenv("HOME"), default_cache_name)

	if args.list_cache:
		cache = cache_load(args.cache_location)
		for entry in cache:
			ts, e = entry
			hosts = e.keys()
			for host in hosts:
				print(ts, host)
		print("!!!xx from cache!!!")
		return


	# only add results to cache if a full analysis was run
	add_to_cache = not args.commandlist

	# run the selected list of commands
	new = local_run(tmpdirname, args.commandlist)

	# load last entry from cache
	cache = Cache(args.cache_location)
	cache.load()
	old = cache.get_last_entry()

	anomalies = []

	# add new entry to cache if needed
	if add_to_cache:
		if not old:
			anomalies.append(commands.W("no cache entry found yet so caching baseline now"))
		cache.add_entry(new)
	else:
		anomalies.append(commands.W("results not cached as only partial list of commands was run"))

	# merge the list of differences with the previous list this is done
	# such that the warnings added above will appear first when outputting
	# the warnings later on in print_anomalies
	anomalies = anomalies + compare_output(old, new, args.commandlist)

	# output the detected anomalies
	print_anomalies(anomalies, args.show_debug)

	# update the cache
	cache.purge(args.max_cache_entries)
	cache.save()

def main():
	with tempfile.TemporaryDirectory() as tmpdirname:
		run(tmpdirname)

if __name__ == "__main__":
	main()
