import os
from datetime import datetime

DATE_PARSE_STR = "%Y-%m-%d %H:%M:%S.%f"

# return a list with unique and sorted set of keys of dictionary d1 and d2
def merge_keys_to_list(d1, d2):
	ret = list(set(list(d1.keys()) + list(d2.keys())))	
	ret.sort()
	return ret

# if subsecs is True we return mili/micro seconds too otherwise just seconds
def ts_to_str(timestamp, subsecs=True):
	return None if not timestamp else timestamp.strftime(DATE_PARSE_STR if subsecs else DATE_PARSE_STR[:-3])

# if subsecs is True we convert mili/micro seconds too otherwise the input
# string is assumed to only contain maximum second precision
def str_to_ts(s, subsecs=True):
	return None if not s else datetime.strptime(s, DATE_PARSE_STR if subsecs else DATE_PARSE_STR[:-3])
