from . import *
from datetime import datetime

PARSE_STR = "%Y-%m-%d %H:%M:%S"

class UptimeCommand(Command):
	name = "uptime"
	shell = False
	command = "uptime -s"

	def parse(output):
		if not output:
			return None 
		try:
			return datetime.strptime(output.strip(), PARSE_STR)
		except ValueError:
			return None

	def compare(prev, cur):
		scur = cur.strftime(PARSE_STR)
		if not prev:
			return [D("system has been up since %s" % scur)]
		if cur != prev and cur > prev:
			return [W("system rebooted since last check (up since: %s)" % scur)]
		else:
			return [D("system didn't reboot since last check (up since: %s)" % scur)]
