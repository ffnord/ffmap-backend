import re
from functools import reduce

def mac_to_hostid(mac):
  int_mac = list(map(lambda x: int(x, 16), mac.split(":")))
  int_mac[0] ^= 2
  bytes = map(lambda x: "%02x" % x, int_mac[0:3] + [0xff, 0xfe] + int_mac[3:])
  return reduce(lambda a, i:
                  [a[0] + ("" if i == 0 else ":") + a[1] + a[2]] + a[3:],
                range(0, 4),
                [""] + list(bytes)
               )

