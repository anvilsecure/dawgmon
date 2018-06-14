from . import *

SYSTEMCTL_BIN = "/bin/systemctl"

def remove_footer_from_table(output):
	# remove the empty lines and footers at the end
	lines = output.splitlines()
	if len(lines) == 0:
		return []
	full_lines = []
	for l in lines:
		if len(l) == 0:
			break
		full_lines.append(l)
	return full_lines

# output tables in systemd are made up relatively uniformly so this function has the ability to parse them into a list of dictionaries with one dictonary for each row. Each dictionary's keys are 
# automatically derived from the table header.
def parse_systemd_output_table(output):
	res = []
	lines = remove_footer_from_table(output)
	if len(lines) == 0:
		return res
	# parse header to get data offsets for entries
	headers = lines[0]
	hs = headers.split()
	offsets = [headers.find(h) for h in hs]
	# use lowercase headers for entries in dict entries
	headers = [h.lower() for h in hs]
	# parse and add each entry ignoring header and last two lines as those are either empty or showing the total entry count
	for line in lines[1:]:
		j = 0
		e = {}
		lo = len(offsets)
		for i, start in enumerate(offsets):
			if i < lo-1:
				end = offsets[i+1]
			else:
				end = len(line)
			e[headers[j]] = line[start:end].strip()
			j = j + 1
		res.append(e)
	return res

class ListSystemDSocketsCommand(Command):
	name = "systemd_sockets"
	shell = False
	command = "%s list-sockets --full" % (SYSTEMCTL_BIN)
	desc = "list systemd sockets"

	def parse(output):
		res = {}
		entries = parse_systemd_output_table(output)
		for e in entries:
			res[e["listen"]] = (e["unit"], e["activates"])
		return res

	def compare(prev, cur):
		anomalies = []
		sockets = merge_keys_to_list(prev, cur)
		for listen in sockets:
			if listen not in prev:
				anomalies.append(C("systemd socket %s added" % listen))
				continue
			elif listen not in cur:
				anomalies.append(C("systemd socket %s removed" % listen))
				continue
			p, c = prev[listen], cur[listen]
			if p[0] != c[0]:
				anomalies.append(C("systemd socket %s came from unit %s but now comes from %s" % (listen, p[0], c[0])))
			if p[1] != c[1]:
				anomalies.append(C("systemd socket %s used to activate %s but now activates %s" % (listen, p[1], c[1])))
		return anomalies

class ListSystemDTimersCommand(Command):
	name = "systemd_timers"
	shell = False
	command = "%s list-timers --all --full" % (SYSTEMCTL_BIN)
	desc = "list systemd timers"

	def parse(output):
		res = {}
		entries = parse_systemd_output_table(output)
		for e in entries:
			res[e["unit"]] = (e["activates"], e["last"], e["next"], e["left"], e["passed"])
		return res

	def compare(prev, cur):
		anomalies = []
		units = merge_keys_to_list(prev, cur)
		for unit in units:
			if unit not in prev:
				anomalies.append(C("systemd timer %s added" % unit))
				continue
			elif unit not in cur:
				anomalies.append(C("systemd timer %s removed" % unit))
				continue
			p, c = prev[unit], cur[unit]
			if p[0] != c[0]:
				anomalies.append(C("systemd timer %s used to activate %s but now %s" % (unit, p[0], c[0])))
			anomalies.append(D("systemd timer %s ran at %s (%s) and will run again at %s (%s)" % (unit, c[1], c[3], c[2], c[4])))
		return anomalies

class ListSystemDUnitsCommand(Command):
	name = "systemd_units"
	shell = False
	command = "%s --all --full" % (SYSTEMCTL_BIN)
	desc = "list all available systemd units"

	def parse(output):
		res = {}
		entries = parse_systemd_output_table(output)
		for e in entries:
			res[e["unit"]] = (e["active"], e["load"], e["sub"], e["description"])
		return res

	def compare(prev, cur):
		anomalies = []
		units = merge_keys_to_list(prev, cur)
		for unit in units:
			if unit not in prev:
				anomalies.append(C("systemd unit '%s' added" % unit))
				continue
			elif unit not in cur:
				anomalies.append(C("systemd unit '%s' removed" % unit))
				continue
			p, c = prev[unit], cur[unit]
			pstatus, cstatus = p[0], c[0]
			if pstatus != cstatus:
				anomalies.append(C("systemd unit '%s' status changed from '%s' to '%s'" % (unit, pstatus, cstatus)))
			pload, cload = p[1], c[1]
			if pload != cload:
				anomalies.append(C("systemd unit '%s' load changed from '%s' to '%s'" % (unit, pload, cload)))
			psub, csub = p[2], c[2]
			if psub != csub:
				anomalies.append(C("systemd unit '%s' sub changed from '%s' to '%s'" % (unit, psub, csub)))
			pdesc, cdesc = p[3], c[3]
			if pdesc != cdesc:
				anomalies.append(C("systemd unit '%s' description changed from '%s' to '%s'" % (unit, pdesc, csub)))
			anomalies.append(D("systemd unit '%s' was '%s' with status '%s' and sub is '%s'" % (unit, cload, cstatus, csub)))
		return anomalies

class ListSystemDUnitFilesCommand(Command):
	name = "systemd_unitfiles"
	shell = False
	command = "%s list-unit-files --all --full" % (SYSTEMCTL_BIN)
	desc = "list all available systemd unit files"

	def parse(output):
		res = {}
		# hack as the header detection won't work otherwise in the utility function used below because there's a space in the first header 'UNIT FILE'
		lines = output.splitlines()
		if len(lines) == 0: # happens for default no output
			return res
		lines[0] = lines[0].replace("UNIT FILE", "UNIT_FILE")
		output = "\n".join(lines)
		entries = parse_systemd_output_table(output)
		for e in entries:
			res[e["unit_file"]] = e["state"]
		return res

	def compare(prev, cur):
		anomalies = []
		units = merge_keys_to_list(prev, cur)
		for unit in units:
			if unit not in prev:
				anomalies.append(C("systemd unit file %s added" % unit))
				continue
			elif unit not in cur:
				anomalies.append(C("systemd unit file %s removed" % unit))
				continue
			p, c = prev[unit], cur[unit]
			if p != c:
				anomalies.append(C("systemd unit file %s status changed from %s to %s" % (unit, p, c)))
			anomalies.append(D("systemd unit file %s has status %s" % (unit, c)))
		return anomalies

class ListSystemDPropertiesCommand(Command):
	name = "systemd_props"
	shell = False
	command = "%s show --all --full" % (SYSTEMCTL_BIN)
	desc = "show all systemd properties"

	def parse(output):
		res = {}
		lines = output.splitlines()
		for line in lines:
			lf = line.find("=")
			name = line[0:lf]
			value = line[lf+1:].strip()
			res[name] = value
		return res

	def compare(prev, cur):
		anomalies = []
		properties = merge_keys_to_list(prev, cur)
		for propname in properties:
			anomalies.append(D("systemd property %s = %s" % (propname, cur[propname])))
			if propname not in prev:
				anomalies.append(C("systemd property %s added" % propname))
				continue
			elif propname not in cur:
				anomalies.append(C("systemd property %s removed" % propname))
				continue
			p, c = prev[propname], cur[propname]
			if p != c:
				anomalies.append(C("systemd property %s changed from %s to %s" % (propname, p, c)))
		return anomalies
