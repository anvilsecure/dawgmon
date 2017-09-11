import subprocess
import commands, utils

def local_run(dirname, commandlist):
	res = {}
	output = utils.get_output_filename(dirname)
	for cmdname in commandlist:
		cmd = commands.COMMAND_CACHE[cmdname]
		subprocess.call("%s > %s" % (cmd.command, output), shell=True)
		with open(output, "r") as fd:
			res[cmd.name] = fd.read()
	return res
