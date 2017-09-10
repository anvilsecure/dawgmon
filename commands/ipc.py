from . import *

def parse_ipcs_output(output):
	res = {}
	lines = output.splitlines()
	for line in lines:
		parts = line.split()
		# ignore non-table rows and the table header
		if len(parts) < 5 or parts[0] == "------" or parts[0] == "key":
			continue
		key = int(parts[0], 16)
		owner, perms, size = parts[2:5]
		res[int(parts[1])] = (key, owner, perms, int(size))
	return res

class ListSharedMemorySegmentsCommand(Command):
	name = "list_shm"
	shell = False
	command = "ipcs -m"

	def parse(output):
		return parse_ipcs_output(output)

	def compare(prev, cur):
		anomalies = []
		segments = merge_keys_to_list(prev, cur)
		for shmid in segments:
			if shmid not in cur:
				anomalies.append(C("shared memory segment %i destroyed" % shmid))
				continue
			elif shmid not in prev:
				anomalies.append(C("shared memory segment %i created" % shmid))
				continue
			p, c = prev[shmid], cur[shmid]
			if p[0] != c[0]:
				anomalies.append(C("key for shared memory segment %i changed from 0x%x to 0x%x" % (shmid, p[0], c[0])))
			if p[1] != c[1]:
				anomalies.append(C("owner of shared memory segment %i changed from %s to %s" % (shmid, p[1], c[1])))
			if p[2] != c[2]:
				anomalies.append(C("permissions for shared memory segment %i changed from %s to %s" % (shmid, p[2], c[2])))
			if p[3] != c[3]:
				anomalies.append(C("size of shared memory segment %i changed from %i to %i" % (shmid, p[3], c[3])))
		return anomalies

class ListSemaphoreArraysCommand(Command):
	name = "list_sem"
	shell = False
	command = "ipcs -s"

	def parse(output):
		return parse_ipcs_output(output)

	def compare(prev, cur):
		anomalies = []
		queues = merge_keys_to_list(prev, cur)
		for q in queues:
			if q not in cur:
				anomalies.append(C("semaphore %i destroyed" % q))
				continue
			elif q not in prev:
				anomalies.append(C("semaphore %i created" % q))
				continue
		return anomalies

class ListMessageQueuesCommand(Command):
	name = "list_msq"
	shell = False
	command = "ipcs -q"

	def parse(output):
		return parse_ipcs_output(output)

	def compare(prev, cur):
		anomalies = []
		queues = merge_keys_to_list(prev, cur)
		for q in queues:
			if q not in cur:
				anomalies.append(C("message queue %i destroyed" % q))
				continue
			elif q not in prev:
				anomalies.append(C("message queue %i created" % q))
				continue
		return anomalies

class ListListeningUNIXSocketsCommand(Command):
	name = "list_unix_ports"
	shell = False
	command = "netstat -lx"

	def parse(output):
		res = {}
		output = output.splitlines()[2:]
		for line in output:
			parts = line.split()[-4:]
			if parts[1] != "LISTENING":
				# simple sanity check
				raise Exception("unexpected output")
			i_node = int(parts[2])
			sock_name = parts[3]
			sock_type = parts[0]
			res[sock_name] = (i_node, sock_type)
		return res

	def compare(prev, cur):
		anomalies = []
		sockets = merge_keys_to_list(prev, cur)
		for sock in sockets:
			if sock not in cur:
				anomalies.append(C("listening UNIX socket %s closed" % sock))
				continue
			elif sock not in prev:
				anomalies.append(C("listening UNIX socket %s opened" % sock))
				continue
			p, c = prev[sock], cur[sock]
			if p[0] != c[0]:
				anomalies.append(C("i-node for listening UNIX socket %s changed from %i to %i" % (sock, p[0], c[0])))
			if p[1] != c[1]:
				anomalies.append(C("type of listening UNIX socket %s changed from %s to %s" % (sock, p[1], c[1])))
		return anomalies
