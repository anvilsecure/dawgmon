# helper routines to turn messages into the right
# types for displayment later
WARNING, DEBUG, CHANGE = 0x1, 0x2, 0x3
from datetime import datetime
def W(s):
	return (WARNING, s, datetime.utcnow())
def D(s):
	return (DEBUG, s, datetime.utcnow())
def C(s):
	return (CHANGE, s, datetime.utcnow())

from utils import merge_keys_to_list

# base Command class
class Command:
	desc = "<unknown description>"
	@classmethod
	def parse(cls, output):
		raise Exception("not implemented for %s" % str(cls))
	@classmethod
	def compare(cls, prev, cur):
		raise Exception("not implemented for %s" % str(cls))


from .block import *
from .debian import *
from .env import *
from .files import *
from .ipc import *
from .mount import *
from .network import *
from .processes import *
from .systemd import *
from .sysv import *
from .ubuntu import *
from .uptime import *
from .users import *
from .version import *
# commands will be executed in the order they appear in this list
COMMANDS = [
	files.CheckBootDirectoryCommand,
	files.CheckEtcDirectoryCommand,
	files.CheckForPipesCommand,
	files.FindSuidBinariesCommand,
	env.EnvironmentVariablesCommand,
	ipc.ListMessageQueuesCommand,
	ipc.ListSemaphoreArraysCommand,
	ipc.ListSharedMemorySegmentsCommand,
	ipc.ListListeningUNIXSocketsCommand,
	mount.MountpointsCommand,
	processes.CheckProcessessCommand,
	systemd.ListSystemDPropertiesCommand,
	systemd.ListSystemDSocketsCommand,
	systemd.ListSystemDTimersCommand,
	systemd.ListSystemDUnitFilesCommand,
	systemd.ListSystemDUnitsCommand,
	sysv.ListSystemVInitJobsCommand,
	ubuntu.IsRestartRequiredCommand,
	debian.ListInstalledPackagesCommand,
	uptime.UptimeCommand,
	users.CheckGroupsCommand,
	users.CheckUsersCommand,
	version.KernelVersionCommand,
	version.LSBVersionCommand,
	network.ListListeningTCPUDPPortsCommand,
	network.ListNetworkInterfacesCommand,
	block.ListBlockDevicesCommand
]

# built up mapping from command names to command classes
COMMAND_CACHE = {}
for cmd in COMMANDS:
	COMMAND_CACHE[cmd.name] = cmd
