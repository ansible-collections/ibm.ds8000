#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (C) 2022 IBM CORPORATION
# Apache License, Version 2.0 (see https://opensource.org/licenses/Apache-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: ds8000_host_port_info
short_description: Return info on DS8000 host ports
description:
  - Return information pertaining to DS8000 host ports.
  - If the optional parameters are not set, information on all host ports on the DS8000 storage system will be returned.
version_added: "1.1.0"
author: NjM3MjY5NzAgNzA3MzA3 (@NjM3MjY5NzAgNzA3MzA3)
options:
  host_port:
    description:
      - List of host port WWPNs to query.
    type: list
    elements: str
  host:
    description:
      - The name of the DS8000 host to query.
    type: str
notes:
  - Supports C(check_mode).
extends_documentation_fragment:
  - ibm.ds8000.ds8000.documentation
'''

EXAMPLES = r'''
- name: get host_port by name
  ibm.ds8000.ds8000_host_port_info:
    hostname: "{{ ds8000_host }}"
    username: "{{ ds8000_username }}"
    password: "{{ ds8000_password }}"
    wwpn: ansible

- name: get all the hosts
  ibm.ds8000.ds8000_host_info:
    hostname: "{{ ds8000_host }}"
    username: "{{ ds8000_username }}"
    password: "{{ ds8000_password }}"
'''

RETURN = r'''
host_ports:
  description: A list of dictionaries describing the host_ports.
  returned: success
  type: list
  elements: dict
  contains:
    addrdiscovery:
        description: The LUN address discovery method used by the host and host port.
        type: str
        sample: 'reportlun'
    host:
        description: The name of the host the host port is assigned to.
        type: str
        sample: 'ansible'
    host_id:
        description: The ID of the host the host port is assigned to.
        type: str
        sample: 'H5'
    state:
        description: The login state of the host.
        type: str
        sample: 'logged in'
    hosttype:
        description: The name of the host type as defined by the operating system.
        type: str
        sample: 'Linux'
    lbs:
        description:
          - The logical block size used by the designated host and host port.
          - Block size is determined by the host type.
        type: str
        sample: '512'
    logical_paths_established:
        description: The number of logical paths established.
        type: int
        sample: 0
    login_ports:
        description: A list containing the IO ports the host port is logged into.
        type: list
        contains:
          port:
            description:  The logged in IO port ID.
            type: str
            sample: 'I0011'
    login_type:
        description: The method used to login.
        type: str
        sample: 'scsi'
    wwnn:
        description: The host port WWNN.
        type: str
        sample: '10000000C9A1BAB2'
    wwpn:
        description: The host port WWPN.
        type: str
        sample: '10000000C9A1BAB2'
  sample: |
    [
        {
            "addrdiscovery": "reportlun",
            "host": "janus",
            "host_id": "H5",
            "hosttype": "pSeries",
            "lbs": "512",
            "logical_path_established": "0",
            "login_ports": [
                "I0131"
            ],
            "login_type": "scsi",
            "state": "logged in",
            "wwnn": "20000090FA8E52DE",
            "wwpn": "10000090FA8E52DE"
        }
    ]
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.ds8000.plugins.module_utils.ds8000 import Ds8000ManagerBase, ds8000_argument_spec

# The REST API returns links. pyds8k representation returns as links or with values containing empty strings.
KEYS_TO_DELETE = ['link']


class hostPortInformer(Ds8000ManagerBase):
    def host_port_info_collector(self):
        host_port_by_id = []
        host_port_by_host = []

        if self.params['host_port']:
            host_port_by_id = []
            for host_port in self.params['host_port']:
                host_port_by_id.append(self.verify_ds8000_object_exist(self.client.get_host_port, port_id=host_port))
            return self.get_ds8000_objects_from_command_output(host_port_by_id)
        elif self.params['host']:
            host = self.verify_ds8000_object_exist(self.client.get_host, host_name=self.params['host'])
            if host:
                # TODO this doesn't work because of the invalid url bug in the REST api
                #     for host_port in host.host_ports:
                #         host_port_by_host.append(self.does_ds8000_object_exist(self.client.get_host_port, port_id=host_port))
                # This results in fewer REST calls, though may not be faster
                host_ports = self.client.get_host_ports()
                for host_port in host_ports:
                    if self._does_host_port_bound_to_host(host_port):
                        host_port_by_host.append(host_port)
                return self.get_ds8000_objects_from_command_output(host_port_by_host)
        else:
            return self.get_ds8000_objects_from_command_output(self.client.get_host_ports())

    def host_port_info(self):
        return self.delete_representation_keys(self.host_port_info_collector(), key_list=KEYS_TO_DELETE)

    def _does_host_port_bound_to_host(self, host_port_object):
        name = self.params['host']
        if host_port_object.host:
            if name in host_port_object.host:
                return True
        return False


def main():
    argument_spec = ds8000_argument_spec()
    argument_spec.update(host_port=dict(type='list', elements='str'), host=dict(type='str'))

    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=[('host_port', 'host')],
        supports_check_mode=True,
    )

    host_port_informer = hostPortInformer(module)

    host_ports = host_port_informer.host_port_info()

    module.exit_json(changed=host_port_informer.changed, host_ports=host_ports)


if __name__ == '__main__':
    main()
