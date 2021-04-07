# -*- coding: utf-8 -*-

# Copyright (c) 2021 Matan Carmeli <matan.carmeli@ibm.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


class ModuleDocFragment(object):
    # Parameters for VMware modules
    DOCUMENTATION = r'''
options:
    hostname:
      description:
      - The hostname or IP address of the dS8000 server.
      type: str
    username:
      description:
      - The username of the dS8000 server.
      type: str
    password:
      description:
      - The password of the dS8000 server.
      type: str
    validate_certs:
      description:
      - Allows connection when SSL certificates are not valid. Set to C(false) when certificates are not trusted.
      type: bool
      default: True
    port:
      description:
      - The port number of the dS8000 server.
      type: str
      default: 8452
    http_schema:
      description:
      - If controlled DS8000 storage is using http or https.
      type: str
      default: https
'''
