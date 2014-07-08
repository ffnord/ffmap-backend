#!/usr/bin/env python3

from distutils.core import setup

setup(name='FFmap',
      version='0.1',
      description='Freifunk map backend',
      url='https://github.com/ffnord/ffmap-backend',
      packages=['ffmap', 'ffmap.inputs', 'ffmap.outputs', 'ffmap.rrd'],
     )
