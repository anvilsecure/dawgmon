import subprocess, shlex
import commands

def local_run(dirname, commandlist):
	for cmdname in commandlist:
		cmd = commands.COMMAND_CACHE[cmdname]

		# shell escape such that we can pass command properly onwards
		# to the Popen call
		cmd_to_execute = shlex.split(cmd.command)

		p = subprocess.Popen(cmd_to_execute, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		stdout, stderr = p.communicate()

		# XXX we should probably try and get the system encoding for
		# this instead of defaulting to UTF-8.
		stdout = stdout.decode("utf-8")
		stderr = stderr.decode("utf-8")

		yield (cmd.name, "$ %s" % " ".join(cmd_to_execute), p.returncode, stdout, stderr)
