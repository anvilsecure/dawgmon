from . import *

# pw entry set to "x" means password is stored in /etc/shadow or /etc/gshadow
# file # and a completely empty entry there means possibly passwordless login
# for either the user or the group in /etc/passwd or /etc/group respectively.
def is_empty(pw):
	return not pw or len(pw) == 0
def is_gshadow(pw):
	return pw and pw == "x"
def anonymize_pw(pw):
	# the two utility functions above will also work if we
	# replace the hash with an anonymous string and the results
	# for all the checks will be the same here
	if is_empty(pw) or is_gshadow(pw):
		return pw
	return "<anonymized>"

class CheckGroupsCommand(Command):
	name = "check_groups"
	shell = False
	command = "cat /etc/group"

	def parse(data):
		data = data.splitlines()
		res = {}
		for line in data:
			parts = line.split(":")
			users = parts[3].split(",")
			if len(users[0]) == 0:
				users = []
			pwhash_entry = anonymize_pw(parts[1])
			res[parts[0]] = (int(parts[2]), users, pwhash_entry)
		return res

	def compare(prev, cur):
		anomalies = []
		groups = merge_keys_to_list(prev, cur)
		shadow_groups = []
		for group in groups:
			if group not in prev:
				anomalies.append(C("group %s added" % group))
				if cur[group][2]:
					shadow_groups.append(group)
				continue
			elif group not in cur:
				anomalies.append(C("group %s removed" % group))
				continue
			prev_gid, cur_gid = prev[group][0], cur[group][0]
			prev_pw, cur_pw = prev[group][2], cur[group][2]
			prev_users, cur_users = prev[group][1], cur[group][1]
			if prev_gid != cur_gid:
				anomalies.append(C("gid of group %s changed from %i to %i" % (group, prev_gid, cur_gid)))
			if is_gshadow(prev_pw) != is_gshadow(cur_pw):
				from_file = "gshadow" if is_gshadow(prev_pw) else "group"
				to_file = "gshadow" if is_gshadow(cur_pw) else "group"
				anomalies.append(C("password for group %s moved from /etc/%s to /etc/%s" % (group, from_file, to_file)))
			if is_gshadow(cur_pw) or is_empty(cur_pw):
				shadow_groups.append(group)
			if is_empty(cur_pw):
				anomalies.append(W("password for group %s set to empty (might allow group login)" % (group)))

			all_users = list(set(prev_users + cur_users))
			for user in all_users:
				if user not in prev_users:
					anomalies.append(C("user %s added to group %s" % (user, group)))
				elif user not in cur_users:
					anomalies.append(C("user %s removed from group %s" % (user, group)))
		in_group = list(set(cur.keys()) ^ set(shadow_groups))
		l = len(in_group)
		if l == 0:
			anomalies.append(D("all groups have entries for passwords in /etc/gshadow as they should"))
			return anomalies
		anomalies.append(W("%i password%s for groups not in /etc/gshadow but /etc/group [%s]" % (l, "s" if l != 1 else "", ",".join(in_group))))
		return anomalies

class CheckUsersCommand(Command):
	name = "check_users"
	shell = False
	command = "cat /etc/passwd"

	def parse(data):
		data = data.splitlines()
		res = {}
		for line in data:
			parts = line.split(":")
			login = parts[0]
			uid, gid = int(parts[2]), int(parts[3])
			homedir, shell = parts[5].strip(), parts[6].strip()
			pwhash_entry = anonymize_pw(parts[1])
			res[login] = (uid, gid, homedir, shell, pwhash_entry)
		return res

	def compare(prev, cur):
		anomalies = []
		users = merge_keys_to_list(prev, cur)
		shadow_users = []
		for user in users:
			if user not in prev:
				anomalies.append(C("user %s added" % user))
				if cur[user][4]:
					shadow_users.append(user)
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
			prev_pw, cur_pw = p[4], c[4]
			if is_gshadow(prev_pw) != is_gshadow(cur_pw):
				from_file = "shadow" if is_gshadow(prev_pw) else "passwd"
				to_file = "shadow" if is_gshadow(cur_pw) else "passwd"
				anomalies.append(C("password for user %s moved from /etc/%s to /etc/%s" % (user, from_file, to_file)))
			if is_gshadow(cur_pw) or is_empty(cur_pw):
				shadow_users.append(user)
			if is_empty(cur_pw):
				anomalies.append(W("password for user %s set to empty (might allow login)" % (user)))

		# for shadow users check we only care about the current file to display warnings
		in_passwd = list(set(cur.keys()) ^ set(shadow_users))
		l = len(in_passwd)
		if l == 0:
			anomalies.append(D("all users have entries for passwords in /etc/shadow file as they should"))
			return anomalies
		anomalies.append(W("%i password%s for users not in /etc/shadow but /etc/passwd [%s]" % (l, "s" if l != 1 else "", ",".join(in_passwd))))
		return anomalies
