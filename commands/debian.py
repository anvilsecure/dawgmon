from . import *


def convert_code_to_string(table, c, desc=False):
	if not c or type(c) != str or len(c) != 1:
		raise ValueError("invalid argument supplied")
	bad = " (bad)" if c.isupper() else ""
	c = c.lower()
	s = table[c][0 if not desc else 1] if c in table else "unknown (%c)" % c
	return "%s%s" % (s, bad)

def error_string(c, desc=False):
	errors = {"r":("Reinst-required", "reinstall required")}
	return convert_code_to_string(errors, c, desc)

def desired_string(c, desc=False):
	desired = {
		"u":("Unknown", "unknown"),
		"i":("Install", "to be installed"),
		"r":("Remove", "to be removed from package list"),
		"p":("Purge", "to be purged from system"),
		"h":("Hold", "to be held")
	}
	return convert_code_to_string(desired, c, desc)

def status_string(c, desc=False):
	statuses = {
		"n":("Not", "unknown"),
		"i":("Inst", "is installed"),
		"c":("Conf-files", "has configuration files"),
		"u":("Unpacked", "is unpacked"),
		"f":("halF-conf", "is half configured"),
		"H":("Half-inst", "is half installed"),
		"w":("trig-aWait", "is awaiting a trigger"),
		"t":("trig-pend", "has a trigger pending")
	}
	return convert_code_to_string(statuses, c, desc)

class ListInstalledPackagesCommand(Command):
	name = "list_packages"
	shell = False
	command = "/usr/bin/dpkg --list"
	desc = "analyze changes in installed Debian packages"

	def parse(output):
		res = {}
		lines = output.splitlines()
		header_done = False
		for line in lines:
			parts = line.split()
			p0 = parts[0]
			if len(p0) >= 3 and p0[0:3] == "+++":
				header_done = True
				continue
			if not header_done:
				continue
			version = parts[2]
			status = parts[0]
			res[parts[1]] = (version, status)
		return res

	def compare(prev, cur):
		anomalies = []
		packages = merge_keys_to_list(prev, cur)
		for package in packages:
			if package not in prev:
				c = cur[package]
				cdesired, cstatus = c[1][0:2]
				anomalies.append(C("package %s is now added (desire is '%s', status is '%s')" % (package, desired_string(cdesired, True), status_string(cstatus, True))))
				continue
			elif package not in cur:
				p = prev[package]
				pdesired, pstatus = p[1][0:2]
				anomalies.append(C("package %s is now removed (status used to be '%s')" % (package, status_string(pstatus, True))))
				continue
			p, c = prev[package], cur[package]
			if p[0] != c[0]:
				anomalies.append(C("package %s version changed from %s to %s" % (package, p[0], c[0])))
			pdesired, pstatus = p[1][0:2]
			cdesired, cstatus = c[1][0:2]
			if pstatus != cstatus:
				anomalies.append(D("package %s status changed from '%s' to '%s'" % (package, status_string(pstatus, True), status_string(cstatus, True)))) 
			if pdesired == cdesired:
				continue
			anomalies.append(C("package %s is %s" % (package, desired_string(cdesired, True))))
		return anomalies
