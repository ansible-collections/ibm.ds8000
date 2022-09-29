#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (C) 2022 IBM CORPORATION
# Apache License, Version 2.0 (see https://opensource.org/licenses/Apache-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: ds8000_host_info
short_description: Return info on DS8000 hosts
description:
  - Return information pertaining to DS8000 hosts.
  - If the optional parameters are not set, information on all hosts on the DS8000 storage system will be returned.
version_added: "1.1.0"
author: NjM3MjY5NzAgNzA3MzA3 (@NjM3MjY5NzAgNzA3MzA3)
options:
  name:
    description: The host name.
    type: str
notes:
  - Supports C(check_mode).
extends_documentation_fragment:
  - ibm.ds8000.ds8000.documentation
'''

EXAMPLES = r'''
- name: get host by name
  ibm.ds8000.ds8000_host_info:
    hostname: "{{ ds8000_host }}"
    username: "{{ ds8000_username }}"
    password: "{{ ds8000_password }}"
    name: ansible

- name: get all the hosts
  ibm.ds8000.ds8000_host_info:
    hostname: "{{ ds8000_host }}"
    username: "{{ ds8000_username }}"
    password: "{{ ds8000_password }}"
'''

RETURN = r'''
hosts:
  description: A list of dictionaries describing the hosts.
  returned: success
  type: list
  elements: dict
  contains:
    name:
      description: The host name.
      type: str
      sample: 'ansible'
    state:
      description:
        - Specifies one of the states of the specified host.
        - If at least one host port is in the logged in state, the state displays as online.
        - If no host ports were added to the specified host, or if all of the added host ports are logged out, the state displays as offline.
      type: str
      sample: 'online'
    hosttype:
      description: The name of the host type as defined by the operating system.
      type: str
      sample: 'Linux'
    addrmode:
      description:
        - The method used by the host to discover the LUNs that are available to its host ports.
        - For example, scsimask, scsimap256, os400mask.
      type: str
      sample: 'scsimap256'
    addrdiscovery:
      description: The LUN address discovery method used by the host system and host system port.
      type: str
      sample: 'lunpolling'
    lbs:
      description:
        - Logical block size of the volumes that the host can access.
        - Block size is determined by the host type.
      type: str
      sample: '512'
    mappings_briefs:
      description: A dictionary describing the volumes mapped to the host.
      type: list
      elements: dict
      contains:
        lunid:
          description: The LUN ID.
          type: str
          sample: '40B04000'
        volume_id:
          description: The volume ID.
          type: str
          sample: 'B000'
    host_ports_briefs:
      description: A dictionary describing the host ports assigned to the host.
      type: list
      elements: dict
      contains:
        wwpn:
          description: The host port WWPN.
          type: str
          sample: '10000090FA8E52DF'
    login_ports:
      description: A list of dictionaries describing IO ports with logins.
      type: list
      elements: dict
      contains:
        id:
          description: The IO port ID.
          type: str
          sample: 'I0000'
        state:
          description: The IO port state.
          type: str
          sample: 'offline'
        wwpn:
          description: The IO port WWPN.
          type: str
          sample: '500507630801054F'
  sample: |
    [
        {
            "addrdiscovery": "reportlun",
            "addrmode": "SCSI mask",
            "host_id": "H5",
            "host_ports_briefs": [
                {
                    "wwpn": "10000090FA8E52DF"
                },
                {
                    "wwpn": "10000090FA8E52DE"
                },
                {
                    "wwpn": "10000090FA8E52EB"
                },
                {
                    "wwpn": "10000090FA8E52EA"
                }
            ],
            "hosttype": "pSeries",
            "lbs": "512",
            "login_ports": [
                {
                    "id": "I0010",
                    "state": "online",
                    "wwpn": "500507630801054C"
                },
                {
                    "id": "I0130",
                    "state": "online",
                    "wwpn": "50050763080B054C"
                }
            ],
            "mappings_briefs": [
                {
                    "lunid": "40B04000",
                    "volume_id": "B000"
                },
                {
                    "lunid": "40B04001",
                    "volume_id": "B001"
                },
                {
                    "lunid": "40B14000",
                    "volume_id": "B100"
                },
                {
                    "lunid": "40B14001",
                    "volume_id": "B101"
                }
            ],
            "name": "ansible",
            "state": "online"
        }
    ]
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.ds8000.plugins.module_utils.ds8000 import Ds8000ManagerBase, ds8000_argument_spec

# The REST API returns links. pyds8k representation returns as links or with values containing empty strings.
KEYS_TO_DELETE = ['link', 'ioports', 'host_ports', 'volumes', 'mappings']


class hostsInformer(Ds8000ManagerBase):
    def host_info_collector(self):
        host_by_name = []

        if self.params['name']:
            host_by_name = self.verify_ds8000_object_exist(self.client.get_host, host_name=self.params['name'])
            return self.get_ds8000_objects_from_command_output(host_by_name)
        else:
            return self.get_ds8000_objects_from_command_output(self.client.get_hosts())

    def host_info(self):
        return self.delete_representation_keys(self.host_info_collector(), key_list=KEYS_TO_DELETE)


def main():
    argument_spec = ds8000_argument_spec()
    argument_spec.update(name=dict(type='str'))

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    host_informer = hostsInformer(module)

    hosts = host_informer.host_info()

    module.exit_json(changed=host_informer.changed, hosts=hosts)


if __name__ == '__main__':
    main()
