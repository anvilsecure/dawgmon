from . import *

def change_attr_list_to_dict(attrs):
	ret = {}
	for attr in attrs:
		lf = attr.find("=")
		val = attr[lf+1:] if lf != -1 else None
		name = attr[0:lf] if lf != -1 else attr
		ret[name] = val
	return ret

class MountpointsCommand(Command):
	name = "list_mount"
	shell = False
	command = "/bin/mount"
	desc = "analyze changes in file system mounts"

	def parse(output):
		lines = output.splitlines()
		if len(lines) == 0:
			return {}
		ret = {}
		for line in lines:
			lf = line.find("on")
			device = line[:lf].strip()
			line = line[lf+3:]
			lf = line.find("type")
			point = line[:lf].strip()
			line = line[lf+5:]
			lf = line.find("(")
			mtype = line[:lf].strip()
			# strip off final ')'
			attrs = [a.strip() for a in line[lf+1:-1].split(",")]
			ret[point] = (device, mtype, attrs)
		return ret

	def compare(prev, cur):
		anomalies = []
		mounts = merge_keys_to_list(prev, cur)
		for mount in mounts:
			if mount not in prev:
				c = cur[mount]
				anomalies.append(C("added mount %s of type %s for device %s (%s)" % (mount, c[1], c[0], ",".join(c[2]))))
				continue
			elif mount not in cur:
				p = prev[mount]
				anomalies.append(C("removed mount %s of type %s for device %s (%s)" % (mount, p[1], p[0], ",".join(p[2]))))
				continue
			p, c = prev[mount], cur[mount]
			if p[0] != c[0]:
				anomalies.append(C("mount %s changed device from %s to %s" % (mount, p[0], c[0])))
			if p[1] != c[1]:
				anomalies.append(C("mount %s changed type from %s to %s" % (mount, p[1], c[1])))
			pattr, cattr = p[2], c[2]
			pattr = change_attr_list_to_dict(pattr)
			cattr = change_attr_list_to_dict(cattr)
			attrs = merge_keys_to_list(pattr, cattr)
			for attr in attrs:
				if attr not in pattr:
					sval = " with value %s" % cattr[attr] if cattr[attr] else ""
					anomalies.append(C("attribute %s got added to mount %s%s" % (attr, mount, sval)))
					continue
				elif attr not in cattr:
					sval = " with value %s" % pattr[attr] if pattr[attr] else ""
					anomalies.append(C("attribute %s was removed from mount %s%s" % (attr, mount, sval)))
					continue
				pa, ca = pattr[attr], cattr[attr]
				if pa != ca:
					pa = pa if pa else "<no value>"
					ca = ca if ca else "<no value>"
					anomalies.append(C("attribute %s for mount %s changed from %s to %s" % (attr, mount, pa, ca)))
			anomalies.append(D("mount %s of type %s for device %s (%s)" % (mount, c[1], c[0], ",".join(c[2]))))
		return anomalies
