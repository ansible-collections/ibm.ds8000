#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (C) 2021 IBM CORPORATION
# Apache License, Version 2.0 (see https://opensource.org/licenses/Apache-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: ds8000_volume_info
short_description: Return basic info on DS8000 volumes
description:
  - Return basic information pertaining to DS8000 volumes.
  - If the optional parameters are not set, information on all volumes on the DS8000 storage system will be returned.
version_added: "1.0.0"
author: Matan Carmeli (@matancarmeli7)
options:
  host:
    description:
      - The host that the volumes are mapped to.
    type: str
  pool:
    description:
      - The pool id that the volumes are belong to.
    type: str
notes:
  - Supports C(check_mode).
extends_documentation_fragment:
  - ibm.ds8000.ds8000.documentation
'''

EXAMPLES = r'''
- name: get all the volumes under host
  ibm.ds8000.ds8000_volume_info:
    hostname: "{{ ds8000_host }}"
    username: "{{ ds8000_username }}"
    password: "{{ ds8000_password }}"
    host: host_name_test

- name: get all the volumes under pool
  ibm.ds8000.ds8000_volume_info:
    hostname: "{{ ds8000_host }}"
    username: "{{ ds8000_username }}"
    password: "{{ ds8000_password }}"
    pool: pool_name_test

- name: get all the volumes
  ibm.ds8000.ds8000_volume_info:
    hostname: "{{ ds8000_host }}"
    username: "{{ ds8000_username }}"
    password: "{{ ds8000_password }}"
'''

RETURN = r'''
volumes:
  description: A list of dictionaries describing the volumes.
  returned: success
  type: list
  sample: [
    {
        "name": "volume_name",
        "id": "volume_id"
    }
  ]
  contains:
    volume:
      description: A dictionary describing the volume properties.
      type: dict
      contains:
        id:
          description: Volume ID.
          type: str
          sample: '1000'
        name:
          description: Volume name.
          type: str
          sample: 'ansible'
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.ds8000.plugins.module_utils.ds8000 import Ds8000ManagerBase, ds8000_argument_spec

DEFAULT_POOLS_URL = '/pools'
DEFAULT_HOSTS_URL = '/hosts'


class VolumesInformer(Ds8000ManagerBase):
    def volume_info(self):
        volumes_by_host = []
        volumes_by_pool = []
        if self.params['host'] and self.verify_ds8000_object_exist(self.client.get_host, host_name=self.params['host']):
            volumes_by_host = self.get_ds8000_objects_from_command_output(self.client.get_volumes_by_host(host_name=self.params['host']))
        if self.params['pool'] and self.verify_ds8000_object_exist(self.client.get_pool, pool_id=self.params['pool']):
            volumes_by_pool = self.get_ds8000_objects_from_command_output(self.client.get_volumes_by_pool(pool_id=self.params['pool']))
        if volumes_by_host and volumes_by_pool:
            volumes_by_pool_and_host = [volume_dict for volume_dict in volumes_by_host if volume_dict in volumes_by_pool]
            return volumes_by_pool_and_host
        elif volumes_by_host and not volumes_by_pool:
            return volumes_by_host
        elif not volumes_by_host and volumes_by_pool:
            return volumes_by_pool
        elif not self.params['host'] and not self.params['pool']:
            return self.get_all_volumes()
        return volumes_by_host


def main():
    argument_spec = ds8000_argument_spec()
    argument_spec.update(host=dict(type='str'), pool=dict(type='str'))

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    volume_informer = VolumesInformer(module)

    volumes = volume_informer.volume_info()

    module.exit_json(changed=volume_informer.changed, volumes=volumes)


if __name__ == '__main__':
    main()
