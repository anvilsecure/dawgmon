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
	desc = "analyze changes in System V shared memory segments"

	def parse(output):
		return parse_ipcs_output(output)

	def compare(prev, cur):
		anomalies = []
		segments = merge_keys_to_list(prev, cur)
		for shmid in segments:
			if shmid not in cur:
				p = prev[shmid]
				anomalies.append(C("shared memory segment %i destroyed (key=0x%x, owner=%s, permissions=%s, size=%i)" % (shmid, p[0], p[1], p[2], p[3])))
				continue
			elif shmid not in prev:
				c = cur[shmid]
				anomalies.append(C("shared memory segment %i created (key=0x%x, owner=%s, permissions=%s, size=%i)" % (shmid, c[0], c[1], c[2], c[3])))
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
			anomalies.append(D("shared memory segment %i (key=0x%x, owner=%s, permissions=%s and size=%i) unchanged" % (shmid, p[0], p[1], p[2], p[3])))
		return anomalies

class ListSemaphoreArraysCommand(Command):
	name = "list_sem"
	shell = False
	command = "ipcs -s"
	desc = "analyze changes in System V sempahores"

	def parse(output):
		return parse_ipcs_output(output)

	def compare(prev, cur):
		anomalies = []
		semaphores = merge_keys_to_list(prev, cur)
		for sem in semaphores:
			if sem not in cur:
				p = prev[sem]
				anomalies.append(C("semaphore array %i destroyed (key=0x%x, owner=%s, permissions=%s, nsems=%i)" % (sem, p[0], p[1], p[2], p[3])))
				continue
			elif sem not in prev:
				c = cur[sem]
				anomalies.append(C("semaphore array %i created (key=0x%x, owner=%s, permissions=%s, nsems=%i)" % (sem, c[0], c[1], c[2], c[3])))
				continue
			p, c = prev[sem], cur[sem]
			if p[0] != c[0]:
				anomalies.append(C("key for semaphore array %i changed from 0x%x to 0x%x" % (sem, p[0], c[0])))
			if p[1] != c[1]:
				anomalies.append(C("owner of semaphore array %i changed from %s to %s" % (sem, p[1], c[1])))
			if p[2] != c[2]:
				anomalies.append(C("permissions for semaphore array %i changed from %s to %s" % (sem, p[2], c[2])))
			if p[3] != c[3]:
				anomalies.append(C("number of semaphores in semaphore array %i changed from %i to %i" % (sem, p[3], c[3])))
			anomalies.append(D("semaphore array %i (key=0x%x, owner=%s, permissions=%s, nsems=%i) unchanged" % (sem, p[0], p[1], p[2], p[3])))
		return anomalies

class ListMessageQueuesCommand(Command):
	name = "list_msq"
	shell = False
	command = "ipcs -q"
	desc = "analyze changes in System V message queues"

	def parse(output):
		return parse_ipcs_output(output)

	def compare(prev, cur):
		anomalies = []
		queues = merge_keys_to_list(prev, cur)
		for q in queues:
			if q not in cur:
				p = prev[q]
				anomalies.append(C("message queue %i destroyed (key=0x%x, owner=%s, permissions=%s, used-bytes=%i)" % (q, p[0], p[1], p[2], p[3])))
				continue
			elif q not in prev:
				c = cur[q]
				anomalies.append(C("message queue %i created (key=0x%x, owner=%s, permissions=%s, used-bytes=%i)" % (q, c[0], c[1], c[2], c[3])))
				continue
			p, c = prev[q], cur[q]
			if p[0] != c[0]:
				anomalies.append(C("key for message queue %i changed from 0x%x to 0x%x" % (q, p[0], c[0])))
			if p[1] != c[1]:
				anomalies.append(C("owner of message queue %i changed from %s to %s" % (q, p[1], c[1])))
			if p[2] != c[2]:
				anomalies.append(C("permissions for message queue %i changed from %s to %s" % (q, p[2], c[2])))
			if p[3] != c[3]:
				anomalies.append(C("used-bytes of message queue %i changed from %i to %i" % (q, p[3], c[3])))
			anomalies.append(D("message queue %i (key=0x%x, owner=%s, permissions=%s, used-bytes=%i) unchanged" % (q, p[0], p[1], p[2], p[3])))
		return anomalies

class ListListeningUNIXSocketsCommand(Command):
	name = "list_unix_ports"
	shell = False
	command = "netstat -lx"
	desc = "list changes in listening UNIX ports"

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
