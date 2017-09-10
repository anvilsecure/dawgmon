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
			res[port] = tuple(set(res[port]))
		return res

	def compare(prev, cur):
		anomalies = []
		ports = merge_keys_to_list(prev, cur)
		for port in ports:
			if port not in cur:
				anomalies.append(C("port %i closed" % port))
			elif port not in prev:
				anomalies.append(C("port %i opened" % port))
		return anomalies
