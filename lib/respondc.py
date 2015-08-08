#!/usr/bin/env python3
import socket
import zlib
import json
import sys


def request(request, targets, interface, timeout=0.5, singleshot=False):
  try:
    if_id = socket.if_nametoindex(interface)
  except OSError:
    print('interface \'{}\' not found'.format(ifname), file=sys.stderr)
    return []

  sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)

  # request
  message = bytes('GET {}'.format(request), 'utf-8')

  for target in targets:
    sock.sendto(message, (target, 1001, 0, if_id))

  print('+ {:s}'.format(str(message)), file=sys.stderr)

  sock.settimeout(timeout)

  # receive
  responses = {}
  rsp, err = 0, 0
  while True:
    print('\r+ {rsp} responses, {err} errors'.format(**locals()), end='', file=sys.stderr)

    try:
      buffer, address = sock.recvfrom(2048)
    except socket.timeout:
      print('\n+ no replies for %f seconds, continuing...' % timeout, file=sys.stderr)
      break

    try:
      source = address[0].split('%')[0]
      data = zlib.decompress(buffer, -15)
      nodeinfo = json.loads(data.decode('utf-8'))
      responses[source] = nodeinfo
      rsp += 1
    except (zlib.error, UnicodeDecodeError, ValueError):
      err += 1
      print('- unreadable answer from {addr}'.format(addr=source), file=sys.stderr)

    if singleshot:
      break

  return responses.values()

