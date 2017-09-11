from . import *

class EnvironmentVariablesCommand(Command):
	name = "env"
	shell = False
	command = "env"

	def parse(output):
		lines = output.splitlines()
		if len(lines) == 0:
			return {}
		ret = {}
		for line in lines:
			lf = line.find("=")
			name = line[:lf].strip()
			value = line[lf+1:].strip()
			ret[name] = value
		return ret

	def compare(prev, cur):
		anomalies = []
		envvars = merge_keys_to_list(prev, cur)	
		for var in envvars:
			if var not in prev:
				anomalies.append(C("environment variable %s added (%s)" % (var, cur[var])))
				continue
			elif var not in cur:
				anomalies.append(C("environment variable %s removed (%s)" % (var, prev[var])))
				continue
			elif prev[var] != cur[var]:
				anomalies.append(C("environment variable %s changed from '%s' to '%s'" % (var, prev[var], cur[var])))
			anomalies.append(D("environment variable %s (%s)" % (var, cur[var])))
		return anomalies
