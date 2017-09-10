from . import *

from datetime import datetime

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
			if len(parts) != 9:
				continue
			fn = parts[8]
			perm = parts[0]
			user, group, size = parts[2:5]
			date, ts, tz = parts[5:8]
			size = int(size)
			# timestamp seems to be given in nano-seconds with Python only
			# supporting up to micro-seconds so we 'divide' by 1000 by simply
			# stripping off the last 3 bytes
			ts = ts[:-3]
			dt = datetime.strptime("%s %s %s" % (date, ts, tz), "%Y-%m-%d %H:%M:%S.%f %z")
			res[fn] = (user, group, size, dt, perm)
		return res

	def compare(prev, cur):
		anomalies = []
		fns = merge_keys_to_list(prev, cur)
		for fn in fns:
			if fn not in cur:
				anomalies.append(C("file %s got unlinked" % fn))
				continue
			elif fn not in prev:
				anomalies.append(C("file %s got created" % fn))
				continue
			p, c = prev[fn], cur[fn]
			if p[0] != c[0]:
				anomalies.append(C("owner of file %s changed from %s to %s" % (fn, p[0], c[0])))
			if p[1] != c[1]:
				anomalies.append(C("group of file %s changed from %s to %s" % (fn, p[1], c[1])))	
			if p[2] != c[2]:
				anomalies.append(C("size of file %s changed from %i to %i" % (fn, p[2], c[2])))
			if p[3] != c[3]:
				anomalies.append(C("file %s got modified on %s" % (fn, c[3].strftime("%Y-%m-%d %H:%M:%S.%f %z"))))
			if p[4] != c[4]:
				anomalies.append(C("permissions for file %s changed from %s to %s" % (fn, p[4], c[4])))
		return anomalies

class CheckEtcDirectoryCommand(CheckFilesInDirectoryCommand):
	name = "check_etc"
	directory = "/etc"
	_command = CheckFilesInDirectoryCommand.command % (directory, "f")
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
		# somewhat dirty hack to make this more descriptive by
		# changing the language for all the named UNIX pipes
		# to state pipe instead of file.
		anomalies = []
		ret = CheckFilesInDirectoryCommand.compare(prev, cur)
		for r in ret:
			# replace first occurence of file to pipe so we only
			# change the description and not an actual filename of
			# a pipe which happens to have the phrase 'file' in it
			anomalies.append((r[0], r[1].replace("file", "pipe", 1)))
		return anomalies

class FindSuidBinariesCommand(CheckFilesInDirectoryCommand):
	name = "find_suids"
	shell = True
	command = "find / -xdev -type f \( -perm -4000 -o -perm -2000 \) -exec ls --full-time -la \{\} \; 2>>/dev/null"

	def compare(prev, cur):
		# somewhat dirty hack to make this more descriptive by
		# changing the language for all the suid binaries to state
		# suid binary instead of file.
		anomalies = []
		ret = CheckFilesInDirectoryCommand.compare(prev, cur)
		for r in ret:
			# replace first occurence of file to suid binary so we only
			# change the description and not an actual filename of
			# a suid binary which happens to have the phrase 'file' in it
			anomalies.append((r[0], r[1].replace("file", "suid binary", 1)))
		return anomalies
