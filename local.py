import os, subprocess
import commands

def get_output_filename(dirname):
	return os.path.join(dirname, "output")

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
