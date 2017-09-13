from . import *

class ListListeningTCPUDPPortsCommand(Command):
	name = "list_tcpudp_ports"
	shell = False
	command = "netstat --tcp --udp -ln"

	def parse(output):
		res = {}
		output = output.splitlines()[2:]
		for line in output:
			proto, addr = line.split()[0:4:3]
			port = int(addr[addr.rfind(":")+1:])
			pe = res.setdefault(port, [])
			pe.append(proto)
		for port in res:
			res[port] = list(set(res[port]))
			res[port].sort()
		return res

	def compare(prev, cur):
		anomalies = []
		ports = merge_keys_to_list(prev, cur)
		for port in ports:
			prev_types = "/".join(prev[port]) if port in prev else None
			cur_types = "/".join(cur[port]) if port in cur else None
			if port not in cur:
				anomalies.append(C("port %i %s closed" % (port, prev_types)))
				continue
			elif port not in prev:
				anomalies.append(C("port %i %s opened" % (port, cur_types)))
				continue
			if prev_types != cur_types:
				anomalies.append(C("port %i is open and changed from %s to %s" % (port, prev_types, cur_types)))
			anomalies.append(D("port %i %s is listening" % (port, cur_types)))
		return anomalies

class ListNetworkInterfacesCommand(Command):
	name = "list_ifaces"
	shell = False
	command = "/bin/ip addr"

	def parse(output):
		res = {}
		linecount = 0
		lines = output.splitlines()
		if len(lines) == 0:
			return res
		# get entry ranges by filtering on the 1:, 2:, 3: output please
		# note that upon inserting and removal of f.e. a USB interface
		# the numbers will still increase so we just need to keep
		# counting with the max count never being possible more than
		# the total amount of lines obviously. so sometimes upon
		# insertion and removal a couple of times one can end up with
		# entry numbers such as 1:, 2:, 5: etc.
		entries = []
		for line in lines:
			for i in range(1, len(lines)):
				s = "%i:" % (i)
				if len(line) >=	len(s) and line[:len(s)] == s:
					entries.append(linecount)
					i = i + 1
					break
			linecount = linecount + 1
		le, ll = len(entries), len(lines)
		for i, entry in enumerate(entries):
			entry_lines = lines[entry:entries[i+1] if i < le-1 else ll]
			s = "%i: " % (i)	
			line0 = entry_lines[0][len(s):]
			iface, *rest = line0.split(":")
			rest = "".join(rest)
			lf = rest.find("state ")
			state, *rest = rest[lf+6:].split()
			# now parse inet and inet6 addrs
			addrs = []
			for entry_line in entry_lines:
				es = entry_line.strip()
				if es.startswith("inet"):
					inettype, addr, *rest = es.split()
					addrs.append((inettype, addr))
			# dict keys on iface with the stat and list of addresses
			res[iface] = (state, set(addrs))
		return res

	def compare(prev, cur):
		anomalies = []
		ifaces = merge_keys_to_list(prev, cur)
		for iface in ifaces:
			if iface not in prev:
				addrlist = ",".join(["%s %s" % (x[0], x[1]) for x in cur[iface][1]])
				anomalies.append(C("network interface %s added with state %s [%s]" % (iface, cur[iface][0], addrlist)))
				continue
			elif iface not in cur:
				addrlist = ",".join(["%s %s" % (x[0], x[1]) for x in prev[iface][1]])
				anomalies.append(C("network interface %s with state %s removed [%s]" % (iface, prev[iface][0], addrlist)))
				continue
			p, c = prev[iface], cur[iface]
			if p[0] != c[0]:
				anomalies.append(C("network interface %s state changed from %s to %s" % (iface, p[0], c[0])))
			paddr, caddr = p[1], c[1]
			diff = paddr ^ caddr
			for d in diff:
				if d not in paddr:
					anomalies.append(C("network interface %s got a new address %s %s" % (iface, d[0], d[1])))
				elif d not in caddr:
					anomalies.append(C("network interface %s had address %s %s removed" % (iface, d[0], d[1])))
			if len(diff) == 0:
				anomalies.append(D("network interface %s with state %s (no change in addresses detected)" % (iface, c[0])))
		return anomalies

