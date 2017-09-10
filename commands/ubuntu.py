from . import *

class IsRestartRequiredCommand(Command):
	name = "needs_restart"
	shell = True 
	command = "if test -f /var/run/reboot-required.pkgs ; then cat /var/run/reboot-required.pkgs; fi"

	def parse(output):
		return output

	def compare(prev, cur):
		if len(cur) > 0:
			return [W("reboot required"), D("reboot required because of packages:\n%s" % cur)]
		return []

class ListInstalledPackagesCommand(Command):
	name = "list_packages"
	shell = False
	command = "/usr/bin/dpkg --list"

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
				anomalies.append(C("package %s added to package list" % package))
				continue
			elif package not in cur:
				anomalies.append(C("package %s removed from package list" % package))
				continue
			p, c = prev[package], cur[package]
			if p[0] != c[0]:
				anomalies.append(C("package %s version changed from %s to %s" % (package, p[0], c[0])))
			pdesired, pstatus = p[1][0:2].lower()
			cdesired, cstatus = c[1][0:2].lower()
			if pdesired == cdesired:
				continue
			if cdesired == "r":
				anomalies.append(C("package %s got uninstalled" % package))	
			elif cdesired == "i":
				anomalies.append(C("package %s got installed" % package))	
			elif cdesired == "p":
				anomalies.append(C("package %s got purged" % package))
			elif cdesired == "h":
				anomalies.append(C("package %s got put on hold" % package))
			else:
				pc = "%s%s" % (pdesired, pstatus)
				cc = "%s%s" % (cdesired, cstatus)
				anomalies.append(C("unknown status change (%s to %s) detected for package %s" % (pc, cc, package)))
		return anomalies
