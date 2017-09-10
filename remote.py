import os, json, functools, subprocess
import commands, utils

def get_hosts_filename(dirname):
	return os.path.join(dirname, "hosts")

def get_playbook_filename(dirname):
	return os.path.join(dirname, "playbook")

def ansible_prepare(dirname, hosts):
	with open(get_hosts_filename(dirname), "w+") as fd:
		fd.write("[hosts]\n%s\n" % "\n".join(hosts))
	with open(get_playbook_filename(dirname), "w+") as fd:
		fd.write("---\n- hosts: hosts\n  tasks:\n")
		for cmd in commands.COMMANDS:
			fd.write("    - name: %s\n      %s: %s\n      ignore_errors: yes\n\n" % (cmd.name, "shell" if cmd.shell else "command", cmd.command))

def ansible_gather_results(dirname):
	outputfn = utils.get_output_filename(dirname)
	with open(outputfn, "r") as fd:
		data = json.load(fd)
	play0 = data["plays"][0]
	play_id = play0["play"]["id"]
	res = {}
	for dt in play0["tasks"]:
		task = dt["task"]
		hosts = dt["hosts"]
		task_name, task_id = task["name"], task["id"]
		# empty string is ansible setup task so ignore it
		if task_name == "":
			continue
		for hostname in hosts:
			hostres = res.setdefault(hostname, {})
			stdout = hosts[hostname]["stdout"]
			hostres[task_name] = stdout
	return res

def ansible_run(dirname):
	hosts, playbook, output = [functools.partial(x, dirname)() for x in [get_hosts_filename, get_playbook_filename, utils.get_output_filename]]
	os.putenv("ANSIBLE_STDOUT_CALLBACK", "json")	
	subprocess.call("ansible-playbook -i %s %s > %s" % (hosts, playbook, output), shell=True)
