from . import *

class KernelVersionCommand(Command):
	name = "kernel_version"
	shell = True
	command = "printf \"`uname -a`\\n`uname -v`\""

	def parse(output):
		lines = output.splitlines()
		if len(lines) != 2:
			return None
		kernel_version = lines[1]
		line = lines[0].split(kernel_version)[0].split()
		kernel_name, hostname, kernel_release = line
		return (kernel_name, hostname, kernel_release, kernel_version)

	def compare(prev, cur):
		ret = []
		if not prev:
			prev = cur

		# a hostname change is something for which we want to see a warning
		if prev[1] != cur[1]:
			ret.append(W("hostname changed from %s to %s" % (prev[1], cur[1])))
		else:
			ret.append(D("kernel version check (hostname) yields %s" % cur[1]))

		# count changes and if we found anything which changed in the
		# kernel's name, version or release information the kernel got
		# updated so output a warning too then.
		c = 0
		if prev[0] != cur[0]:
			ret.append(C("kernel name changed from %s to %s" % (prev[0], cur[0])))
			c = c + 1
		else:
			ret.append(D("kernel version check (kernel name) yields %s" % cur[0]))
		if prev[2] != cur[2]:
			ret.append(C("kernel release changed from %s to %s" % (prev[2], cur[2])))
			c = c + 1
		else:
			ret.append(D("kernel version check (kernel release) yields %s" % cur[2]))
		if prev[3] != cur[3]:
			ret.append(C("kernel version changed from %s to %s" % (prev[3], cur[3])))
			c = c + 1
		else:
			ret.append(D("kernel version check (kernel version) yields %s" % cur[3]))

		# if we see a count of > 0 it means something in the kernel has
		# changed so output a warning
		if c > 0:
			ret.append(W("kernel seems to have changed from %s to %s" % (" ".join(prev), " ".join(cur))))
		return ret
