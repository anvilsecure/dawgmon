from . import Command, C

class KernelVersionCommand(Command):
	name = "uname"
	shell = False
	command = "uname -a"

	@classmethod
	def compare(cls, prev, cur):
		prev = prev.strip()
		cur = cur.strip()
		if prev == cur:
			return []
		return [C("system version changed from %s to %s" % (prev, cur))]
