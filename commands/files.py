from . import *

from datetime import datetime

DATE_PARSE_STR = "%Y-%m-%d %H:%M:%S.%f %z"

# XXX we got probably improve this matching a lot if we also start taking the
# inodes into account but we don't right now and just simply do a 'visual'
# compare which should be sufficient in most cases; we're basically automating
# what a system administrator might do by hand when comparing directory
# listings via something like ls -lha etc.

class CheckFilesInDirectoryCommand(Command):
	shell = True
	needs_subclass = True

	# command option --full-time is GNU file utils specific
	# two arguments should be start directory and file type (pipe, symlink, regular file etc)
	command = "find %s -type %s -exec ls --full-time -la \{\} \; 2>>/dev/null"

	def parse(output):
		res = {}
		lines = output.splitlines()
		for line in lines:
			parts = line.split()
			lp = len(parts)
			if lp != 9 and lp != 11:
				continue
			if lp == 11:
				if parts[9] != "->":
					# not a symlink? unexpected output
					# just ignore this line
					print("ignoring symlink??? :(((")
					continue
				symlink = parts[10]
			else:
				symlink = None
			fn = parts[8]
			perm = parts[0]
			user, group, size = parts[2:5]
			date, ts, tz = parts[5:8]
			size = int(size)
			# timestamp seems to be given in nano-seconds with Python only
			# supporting up to micro-seconds so we 'divide' by 1000 by simply
			# stripping off the last 3 bytes
			ts = ts[:-3]
			dt = datetime.strptime("%s %s %s" % (date, ts, tz), DATE_PARSE_STR)
			res[fn] = (user, group, size, dt, perm, symlink)
		return res

	def compare(prev, cur, desc="file"):
		# the description parameter is a somewhat dirty hack to make
		# this more descriptive by changing the language for all the
		# files to state for example suid binary if the caller passed
		# that in here.
		anomalies = []
		fns = merge_keys_to_list(prev, cur)
		for fn in fns:
			if fn not in cur:
				p = prev[fn]
				anomalies.append(C("%s %s got unlinked (owner=%s, group=%s, perm=%s, size=%i)" % (desc, fn, p[0], p[1], p[4], p[2])))
				continue
			elif fn not in prev:
				c = cur[fn]
				anomalies.append(C("%s %s got created (owner=%s, group=%s, perm=%s, size=%i)" % (desc, fn, c[0], c[1], c[4], c[2])))
				continue
			p, c = prev[fn], cur[fn]
			if p[0] != c[0]:
				anomalies.append(C("owner of %s %s changed from %s to %s" % (desc, fn, p[0], c[0])))
			if p[1] != c[1]:
				anomalies.append(C("group of %s %s changed from %s to %s" % (desc, fn, p[1], c[1])))
			if p[2] != c[2]:
				anomalies.append(C("size of %s %s changed from %i to %i" % (desc, fn, p[2], c[2])))
			if p[3] != c[3]:
				cs = c[3].strftime(DATE_PARSE_STR)
				anomalies.append(C("%s %s got modified on %s" % (desc, fn, cs)))
				if p[3] > c[3]:
					ps = p[3].strftime(DATE_PARSE_STR)
					anomalies.append(W("time traveling detected as %s %s got modified previously at %s and now at %s" % (desc, fn, ps, cs)))
			if p[4] != c[4]:
				anomalies.append(C("permissions for %s %s changed from %s to %s" % (desc, fn, p[4], c[4])))
			if p[5] != c[5]:
				if p[5] is None:
					anomalies.append(C("%s %s changed into a symlink pointing to %s" % (desc, fn, c[5])))
				elif c[5] is None:
					anomalies.append(C("%s %s used to be a symlnk pointed to %s but is a regular file now" % (desc, fn, p[5])))
				else:
					anomalies.append(C("%s %s symlink changed pointing from %s to %s" % (desc, fn, p[5], c[5])))
		return anomalies

class CheckEtcDirectoryCommand(CheckFilesInDirectoryCommand):
	name = "check_etc"
	command = "find /etc -xdev \( -type l -o -type f  \) -exec ls --full-time -la \{\} \; 2>>/dev/null"

class CheckBootDirectoryCommand(CheckFilesInDirectoryCommand):
	name = "check_boot"
	directory = "/boot"
	command = CheckFilesInDirectoryCommand.command % (directory, "f")

class CheckForPipesCommand(CheckFilesInDirectoryCommand):
	name = "check_pipes"
	directory = "/"
	command = CheckFilesInDirectoryCommand.command % (directory, "p")

	def compare(prev, cur):
		return CheckFilesInDirectoryCommand.compare(prev, cur, "pipe")

class FindSuidBinariesCommand(CheckFilesInDirectoryCommand):
	name = "find_suids"
	shell = True
	command = "find / -xdev -type f \( -perm -4000 -o -perm -2000 \) -exec ls --full-time -la \{\} \; 2>>/dev/null"

	def compare(prev, cur):
		return CheckFilesInDirectoryCommand.compare(prev, cur, "suid binary")
