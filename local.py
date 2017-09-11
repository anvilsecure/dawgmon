import subprocess
import commands, utils

def local_run(dirname, commandlist=None):
	res = {}
	output = utils.get_output_filename(dirname)
	for cmd in commands.COMMANDS:
		if commandlist and cmd.name not in commandlist:
			continue	
		subprocess.call("%s > %s" % (cmd.command, output), shell=True)
		with open(output, "r") as fd:
			res[cmd.name] = fd.read()
	return res
