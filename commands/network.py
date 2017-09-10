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
