# -*- coding: utf-8 -*-

# Copyright (C) 2021 IBM CORPORATION
# Apache License, Version 2.0 (see https://opensource.org/licenses/Apache-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


class ModuleDocFragment(object):
    # Parameters for IBM DS8000 modules
    DOCUMENTATION = r'''
options:
  hostname:
    description:
    - The hostname or IP address of the DS8000 storage system HMC.
    required: true
    type: str
  username:
    description:
    - The username for the DS8000 storage system.
    required: true
    type: str
  password:
    description:
    - The password for the DS8000 storage system I(username).
    required: true
    type: str
  validate_certs:
    description:
    - Controls validation of SSL chain of trust.
    - Set to C(no) to allow connection when SSL certificates are not trusted.
    type: bool
    default: yes
  port:
    description:
    - The port number of the DS8000 storage system HMC.
    type: str
    default: 8452
requirements:
  - pyds8k >= 1.4.0
  - python >= 3.6
'''
