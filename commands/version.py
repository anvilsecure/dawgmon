from . import Command, C

class KernelVersionCommand(Command):
	name = "uname"
	shell = False
	command = "uname -a"

	def parse(output):
		return output.strip()

	def compare(prev, cur):
		if prev == cur:
			return []
		return [C("system version changed from %s to %s" % (prev, cur))]
