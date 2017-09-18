from . import *

class ListBlockDevicesCommand(Command):
	name = "list_blkdev"
	shell = False
	command = "/bin/lsblk -la"
	desc = "analyze changes in available block devices"

	def parse(output):
		lines = output.splitlines()
		if len(lines) == 0:
			return {}
		ret = {}
		header = lines[0]
		lines = lines[1:]
		for line in lines:
			e = [s.strip() for s in line.split()]
			le = len(e)
			if le == 5:
				name, maj_min, rm, ro, blktype = e[0:5]
				size = "0" # needs to be string to be in line with the size strings from the tool output
			elif le == 6 or le == 7:
				name, maj_min, rm, size, ro, blktype = e[0:6]
			mount = e[6] if len(e) == 7 else None
			ret[e[0]] = (maj_min, int(rm), size, int(ro), blktype, mount)	
		return ret

	def compare(prev, cur):
		anomalies = []
		blocks = merge_keys_to_list(prev, cur)
		for blk in blocks:
			if blk not in prev:
				maj_min, rm, size, ro, blktype, mount = cur[blk]
				anomalies.append(C("block device %s added (type=%s, size=%s, mount=%s, maj:min=%s)" % (blk, blktype, size, mount, maj_min)))
				continue
			elif blk not in cur:
				maj_min, rm, size, ro, blktype, mount = prev[blk]
				anomalies.append(C("block device %s removed (type=%s, size=%s, mount=%s, maj:min=%s)" % (blk, blktype, size, mount, maj_min)))
				continue
			p, c = prev[blk], cur[blk]
			if p[0] != c[0]:
				anomalies.append(C("block device %s had maj:min change from %s to %s" % (blk, p[0], c[0])))
			if p[1] != c[1]:
				anomalies.append(C("block device %s had RM change from %s to %s" % (blk, p[1], c[1])))
			if p[2] != c[2]:
				anomalies.append(C("block device %s had its size changed from %s to %s" % (blk, p[2], c[2])))	
			if p[3] != c[3]:
				anomalies.append(C("block device %s had RO change from %s to %s" % (blk, p[3], c[3])))	
			if p[4] != c[4]:
				anomalies.append(C("block device %s had its type changed from %s to %s" % (blk, p[4], c[4])))	
			if p[5] != c[5]:
				anomalies.append(C("block device %s had its mount changed from %s to %s" % (blk, p[5], c[5])))	
			maj_min, rm, size, ro, blktype, mount = cur[blk]
			anomalies.append(D("block device %s (type=%s, size=%s, mount=%s, maj:min=%s)" % (blk, blktype, size, mount, maj_min)))
		return anomalies
