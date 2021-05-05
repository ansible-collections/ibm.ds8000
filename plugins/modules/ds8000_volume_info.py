#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2021, Matan Carmeli <matan.carmeli7@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
author: Matan Carmeli (@matancarmeli7)
module: ds8000_volume_info
short_description: Return basic info on DS8000 volumes
description:
  - Return basic information pertaining to a DS8000 volumes.
  - If the host and pool parameters are not set, it will give information on all the volumes in the storage.
options:
  host:
    description:
      - The host that the volumes are mapped to.
    type: str
  pool:
    description:
      - The pool that the volumes are belong to.
    type: str
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
virtual_machines:
  description: list of dictionary of volumes and their information
  returned: success
  type: list
  sample: [
    {
        "name": "volume_name",
        "id": "volume_id"
    }
  ]
'''
import json

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.ibm.ds8000.plugins.module_utils.ds8000 import BaseDs8000Manager, ds8000_argument_spec

DEFAULT_POOLS_URL = '/pools'
DEFAULT_HOSTS_URL = '/hosts'


class VolumesInformer(BaseDs8000Manager):
    def ds8000_volume_info(self):
        volumes_by_host = []
        volumes_by_pool = []
        if self.params['host'] and self.verify_ds8000_object_exist('host', 'hosts'):
            volumes_by_host = self.get_ds8000_objects_by_type(
                '/hosts/{hosts}/volumes'.format(hosts=self.params['host']), 'volumes')
        if self.params['pool'] and self.verify_ds8000_object_exist('pool', 'pools'):
            volumes_by_pool = self.get_ds8000_objects_by_type(
                '/pools/{pool}/volumes'.format(pool=self.params['pool']), 'volumes')
        if volumes_by_host and volumes_by_pool:
            volumes_by_pool_and_host = [
                volume_dict for volume_dict in volumes_by_host if volume_dict in volumes_by_pool]
            return volumes_by_pool_and_host
        elif volumes_by_host and not volumes_by_pool:
            return volumes_by_host
        elif not volumes_by_host and volumes_by_pool:
            return volumes_by_pool
        else:
            return self.get_all_volumes()


def main():
    argument_spec = ds8000_argument_spec()
    argument_spec.update(
        host=dict(type='str'),
        pool=dict(type='str')
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
    )

    volume_informer = VolumesInformer(module)

    volumes = volume_informer.ds8000_volume_info()

    module.exit_json(changed=volume_informer.changed, volumes=volumes)


if __name__ == '__main__':
    main()
