from . import *

class ListSystemVInitJobsCommand(Command):
	name = "list_sysvinit_jobs"
	shell = False
	command = "/usr/sbin/service --status-all"

	def parse(output):
		res = {}
		lines = output.splitlines()
		for line in lines:
			parts = line.split()
			res[parts[3]] = parts[1]
		return res

	def compare(prev, cur):
		anomalies = []
		services = merge_keys_to_list(prev, cur)
		for service in services:
			if service not in prev:	
				anomalies.append(C("sysvinit job %s added" % service))
				continue
			elif service not in cur:
				anomalies.append(C("sysvinit job %s removed" % service))
				continue
			p, c = prev[service], cur[service]
			if p == c:
				continue
			if p == "+" and c == "-":
				s = "stopped"
			elif p =="-" and c == "+":
				s = "started"
			else:
				s = "unknown"
			anomalies.append(C("sysvinit job %s %s" % (service, s)))
		return anomalies
