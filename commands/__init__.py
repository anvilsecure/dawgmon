# helper routines to turn messages into the right
# types for displayment later
WARNING, DEBUG, CHANGE = 0x1, 0x2, 0x3
def W(s):
	return (WARNING, s)
def D(s):
	return (DEBUG, s)
def C(s):
	return (CHANGE, s)

# return a list with unique and sorted set of keys of dictionary d1 and d2
def merge_keys_to_list(d1, d2):
	ret = list(set(list(d1.keys()) + list(d2.keys())))	
	ret.sort()
	return ret

# base Command class
class Command:
	@classmethod
	def compare(cls, prev, cur):
		raise Exception("not implemented for %s" % cls)

from .files import *
from .ipc import *
from .processes import *
from .systemd import *
from .ubuntu import *
from .uptime import *
from .users import *
from .version import *
from .network import *

# commands will be executed in the order they appear in this list
COMMANDS = [
	files.CheckBootDirectoryCommand,
	files.CheckEtcDirectoryCommand,
	files.CheckForPipesCommand,
	files.FindSuidBinariesCommand,
	ipc.ListMessageQueuesCommand,
	ipc.ListSemaphoreArraysCommand,
	ipc.ListSharedMemorySegmentsCommand,
	processes.CheckProcessessCommand,
	systemd.ListSystemDServicesCommand,
	ubuntu.IsRestartRequiredCommand,
	ubuntu.ListInstalledPackagesCommand,
	uptime.UptimeCommand,
	users.CheckGroupsCommand,
	users.CheckUsersCommand,
	version.KernelVersionCommand,
	network.ListListeningTCPUDPPortsCommand,
	ipc.ListListeningUNIXSocketsCommand
]

"""
"""

# built up mapping from command names to command classes
COMMAND_CACHE = {}
for cmd in COMMANDS:
	COMMAND_CACHE[cmd.name] = cmd
