from . import *
import time

class UptimeCommand(Command):
	name = "uptime"
	shell = False
	command = "uptime -s"

	@classmethod
	def compare(cls, prev, cur):
		parse_str = "%Y-%m-%d %H:%M:%S"
		prev = prev.strip()
		cur = cur.strip()
		dcur = time.strptime(cur, parse_str)
		# if nothing cached yet we need to prevent parsing errors
		dprev = time.strptime(prev, parse_str) if prev != "" else None
		if not dprev:
			return [D("system has been up since %s" % cur)]
		if dcur != dprev and dcur > dprev:
			return [W("system rebooted since last check (up since: %s)" % cur)]
		else:
			return [D("system didn't reboot since last check (up since: %s)" % cur)]
