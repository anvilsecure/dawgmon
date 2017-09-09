#!/usr/bin/env python3

import sys, os, tempfile, subprocess
import json, functools, pickle, time
from datetime import datetime

import commands
from commands import merge_keys_to_list

VERSION = "0.2a"

def get_hosts_filename(dirname):
	return os.path.join(dirname, "hosts")

def get_playbook_filename(dirname):
	return os.path.join(dirname, "playbook")

def get_output_filename(dirname):
	return os.path.join(dirname, "output")

def ansible_prepare(dirname, hosts):
	with open(get_hosts_filename(dirname), "w+") as fd:
		fd.write("[hosts]\n%s\n" % "\n".join(hosts))
	with open(get_playbook_filename(dirname), "w+") as fd:
		fd.write("---\n- hosts: hosts\n  tasks:\n")
		for cmd in COMMANDS:
			fd.write("    - name: %s\n      %s: %s\n      ignore_errors: yes\n\n" % (cmd.name, "shell" if cmd.shell else "command", cmd.command))

def ansible_run(dirname):
	hosts, playbook, output = [functools.partial(x, dirname)() for x in [get_hosts_filename, get_playbook_filename, get_output_filename]]
	os.putenv("ANSIBLE_STDOUT_CALLBACK", "json")	
	subprocess.call("ansible-playbook -i %s %s > %s" % (hosts, playbook, output), shell=True)

def local_run(dirname, commandlist=None):
	res = {}
	res["localhost"] = {}
	rl = res["localhost"]
	output = get_output_filename(dirname)
	for cmd in commands.COMMANDS:
		if commandlist and cmd.name not in commandlist:
			continue	
		subprocess.call("%s > %s" % (cmd.command, output), shell=True)
		with open(output, "r") as fd:
			rl[cmd.name] = fd.read()
	return res

def ansible_gather_results(outputfn):
	with open(outputfn, "r") as fd:
		data = json.load(fd)
	play0 = data["plays"][0]
	play_id = play0["play"]["id"]
	res = {}
	for dt in play0["tasks"]:
		task = dt["task"]
		hosts = dt["hosts"]
		task_name, task_id = task["name"], task["id"]
		# empty string is ansible setup task so ignore it
		if task_name == "":
			continue
		for hostname in hosts:
			hostres = res.setdefault(hostname, {})
			stdout = hosts[hostname]["stdout"]
			hostres[task_name] = stdout
	return res

def load_cache(fn):
	try:
		with open(fn, "rb") as fd:
			data = pickle.load(fd)
	except FileNotFoundError:
		return []
	return data

def save_cache(data, fn):
	with open(fn, "w+b") as fd:
		pickle.dump(data, fd)

def compare_hosts(old, new, commandlist=None):
	anomalies = []
	tasks = merge_keys_to_list(old, new)
	for task_name in tasks:
		cmd = commands.COMMAND_CACHE.get(task_name, None)
		if not cmd:
			print("unknown task_name specified")
			continue
		if commandlist and task_name not in commandlist:
			print("filtering out %s" % task_name)
			continue
	
		old_data = old[task_name] if task_name in old else ""
		ret = cmd.compare(old_data, new[task_name])
		if type(ret) != list:
			raise Exception("unexpected return value type for %s" % cmd)
		if ret and len(ret) > 0:
			anomalies = anomalies + ret
	return anomalies

def compare_output(old, new, commandlist=None):
	anomalies = {}
	hosts = merge_keys_to_list(old, new)
	for host in hosts:
		if host not in new:
			print("host removed from the host list %s" % host)
			continue
		old_data = old[host] if host in old else {}
		anomalies[host] = compare_hosts(old_data, new[host], commandlist)
	return anomalies

def print_anomalies(anomalies, show_debug=False):
	for host in anomalies:
		ah = anomalies[host]

		changes = list(filter(lambda x:x[0] == commands.CHANGE, ah))
		warning = list(filter(lambda x:x[0] == commands.WARNING, ah))
		debug = list(filter(lambda x:x[0] == commands.DEBUG, ah)) if show_debug else []
		la, lw, ld = len(changes), len(warning), len(debug)
		debugs = " and %i debug message%s" % (ld, "s" if ld != 1 else "") if ld > 0 else ""
		print("[+] %s: %i change%s detected (%i warning%s%s)" % (host, la, "s" if la != 1 else "", lw, "s" if lw != 1 else "", debugs))

		for w in warning:
			print(" !  %s" % w[1])
		for c in changes:
			print(" +  %s" % c[1])
		if show_debug:
			for d in debug:
				print(" -  %s" % d[1])

def run(tmpdirname):
	from argparse import ArgumentParser
	default_max_cache_entries = 64
	parser = ArgumentParser(description="attack surface analyzer and change monitor")
	parser.add_argument("-v", "--version", action="version", version=VERSION)
	parser.add_argument("-H", "--host", help="", action="append", dest="use_ansible", metavar="host")
	parser.add_argument("-L", help="list cache entries", dest="list_cache", action="store_true", default=False)
	parser.add_argument("-c", help="location of cache (default: $CWD/cache.db)", dest="cache_location", metavar="filename", default="./cache.db", required=False)
	parser.add_argument("-e", help="execute specific command", dest="commandlist", metavar="command", type=str, action="append")
	parser.add_argument("-d", help="show debug output", dest="show_debug", action="store_true", default=False)
	parser.add_argument("-m", help="max amount of cache entries per host (default: %i)" % default_max_cache_entries,
		dest="max_cache_entries", type=int, metavar="N", default=default_max_cache_entries, required=False)

	args = parser.parse_args()

	if args.max_cache_entries < 1 or args.max_cache_entries > 1024:
		print("maximum number of cache entries invalid or set too high [1-1024]")
		return

	if args.list_cache:
		cache = load_cache(args.cache_location)
		for entry in cache:
			ts, e = entry
			hosts = e.keys()
			for host in hosts:
				print(ts, host)
		print("!!!xx from cache!!!")
		return

	# determine whether we need to do an ansible run over a list of hosts or just
	# run all the commands on the local machine
	contains_localhost = False
	if args.use_ansible:
		contains_localhost = functools.reduce(lambda x,y:x or y, map(lambda x:x=="localhost", args.use_ansible))
	if contains_localhost:
		print("localhost set so ignoring all remote hosts (if any)")

	# run the commands on the remote set of machines via ansible or locally
	if args.use_ansible != None and not contains_localhost:
		hosts = args.use_ansible
		ansible_prepare(tmpdirname, hosts)
		ansible_run(tmpdirname)
		new = ansible_gather_results(get_output_filename(tmpdirname))
	else:
		new = local_run(tmpdirname, args.commandlist)

	cache = load_cache(args.cache_location)
	ts, old = cache[-1] if len(cache) > 0 else ("1970-01-01 00:00:00", {})
	anomalies = compare_output(old, new, args.commandlist)

	print_anomalies(anomalies, args.show_debug)

	tsnow = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
	cache.append((tsnow, new))
	cache = cache[-args.max_cache_entries:]
	save_cache(cache, args.cache_location)

if __name__ == "__main__":
	with tempfile.TemporaryDirectory() as tmpdirname:
		run(tmpdirname)
