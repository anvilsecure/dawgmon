from . import *

class CheckGroupsCommand(Command):
	name = "check_groups"
	shell = False
	command = "cat /etc/group"

	def convert_to_dict(data):
		data = data.splitlines()
		res = {}
		for line in data:
			parts = line.split(":")
			users = parts[3].split(",")
			if len(users[0]) == 0:
				users = []
			res[parts[0]] = (int(parts[2]), users)
		return res

	@classmethod
	def compare(cls, prev, cur):
		anomalies = []
		prev, cur = cls.convert_to_dict(prev), cls.convert_to_dict(cur)
		groups = merge_keys_to_list(prev, cur)
		for group in groups:
			if group not in prev:
				anomalies.append(C("group %s added" % group))
				continue
			elif group not in cur:
				anomalies.append(C("group %s removed" % group))
				continue
			prev_gid, cur_gid = prev[group][0], cur[group][0]
			if prev_gid != cur_gid:
				anomalies.append(C("gid of group %s changed from %i to %i" % (group, prev_gid, cur_gid)))
			prev_users, cur_users = prev[group][1], cur[group][1]
			all_users = list(set(prev_users + cur_users))
			for user in all_users:
				if user not in prev_users:
					anomalies.append(C("user %s added to group %s" % (user, group)))
				elif user not in cur_users:
					anomalies.append(C("user %s removed from group %s" % (user, group)))
		return anomalies

class CheckUsersCommand(Command):
	name = "check_users"
	shell = False
	command = "cat /etc/passwd"

	def convert_to_dict(data):
		data = data.splitlines()
		res = {}
		for line in data:
			parts = line.split(":")
			login = parts[0]
			uid, gid = int(parts[2]), int(parts[3])
			homedir, shell = parts[5].strip(), parts[6].strip()
			res[login] = (uid, gid, homedir, shell)
		return res

	@classmethod
	def compare(cls, prev, cur):
		anomalies = []
		prev, cur = cls.convert_to_dict(prev), cls.convert_to_dict(cur)
		users = merge_keys_to_list(prev, cur)
		for user in users:
			if user not in prev:
				anomalies.append(C("user %s added" % user))
				continue
			elif user not in cur:
				anomalies.append(C("user %s removed" % user))
				continue
			p, c = prev[user], cur[user]
			if p[0] != c[0]:
				anomalies.append(C("uid for user %s changed from %i to %i" % (user, p[0], c[0])))
			if p[1] != c[1]:
				anomalies.append(C("gid for user %s changed from %i to %i" % (user, p[1], c[1])))
			if p[2] != c[2]:
				anomalies.append(C("homedir for user %s changed from %s to %s" % (user, p[2], c[2])))
			if p[3] != c[3]:
				anomalies.append(C("shell for user %s changed from %s to %s" % (user, p[3], c[3])))
		return anomalies
