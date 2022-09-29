#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (C) 2022 IBM CORPORATION
# Apache License, Version 2.0 (see https://opensource.org/licenses/Apache-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: ds8000_pool_info
short_description: Return info on DS8000 pools
description:
  - Return information pertaining to DS8000 pools.
  - If the optional parameters are not set, information on all pools on the DS8000 storage system will be returned.
version_added: "1.1.0"
author: NjM3MjY5NzAgNzA3MzA3 (@NjM3MjY5NzAgNzA3MzA3)
options:
  id:
    description:
        - The pool id.
    type: str
    aliases: [ pool ]
notes:
  - Supports C(check_mode).
extends_documentation_fragment:
  - ibm.ds8000.ds8000.documentation
'''

EXAMPLES = r'''
- name: get pool id P0
  ibm.ds8000.ds8000_pool_info:
    hostname: "{{ ds8000_host }}"
    username: "{{ ds8000_username }}"
    password: "{{ ds8000_password }}"
    id: P0

- name: get all the pools
  ibm.ds8000.ds8000_pool_info:
    hostname: "{{ ds8000_host }}"
    username: "{{ ds8000_username }}"
    password: "{{ ds8000_password }}"
'''

RETURN = r'''
pools:
  description: A list of dictionaries describing the pools.
  returned: success
  type: list
  elements: dict
  contains:
    id:
      description: The pool ID.
      type: str
      sample: 'P0'
    name:
      description: The pool name.
      type: str
      sample: 'ansible'
    state:
      description:  The pool state.
      type: str
      sample: 'normal'
    cap:
      description: The pool capacity.
      type: int
      sample: 17592186044416
    cap_gb:
      description: The pool capcity in GB.
      type: int
      sample: 16384
    cap_gib:
      description: The pool capacity in GiB.
      type: float
      sample: 17592.2
    real_cap:
      description: The real capacity used by the pool.
      type: int
      sample: 4624471818240
    virtual_cap:
      description: The virtual capacity allocated to the pool.
      type: int
      sample: 17592186044416
    stgtype:
      description: The storage type of the pool.
      type: str
      sample: 'fb'
    VOLSER:
      description:
        - The pool serial number.
        - A pool serial number is 6 bytes of data, displayed as 6 characters.
      type: str
      sample: '0X5000'
    allocmethod:
      description: The extent allocation method.
      type: str
      sample: 'managed'
    tp:
      description: The thin provisioning method.
      type: str
      sample: 'ese'
    capalloc:
      description: The allocated real capacity number.
      type: int
      sample: 4624471818240
    MTM:
      description: The pool device type and the machine type.
      type: str
      sample: '2107-900'
    datatype:
      description: The pool data type.
      type: str
      sample: 'FB 512T'
    easytier:
      description: The state of management by Easy Tier.
      type: str
      sample: 'managed'
    tieralloc:
      description: A list of dictionaries describing the tier allocation.
      type: list
      elements: dict
      contains:
        tier:
          description:  The tier class.
          type: str
          sample: 'SSD'
        allocated:
          description: The capacity allocated to the tier.
          type: int
          sample: 4944866312192
    lss:
      description: The lss ID the pool belongs to.
      type: str
      sample: 'A0'
    pool:
      description: The pool ID the pool belongs to.
      type: str
      sample: 'P0'
  sample: |
    [
          {
              "MTM": "2107-900",
              "VOLSER": "",
              "allocmethod": "managed",
              "cap": "17592186044416",
              "cap_gb": "16384",
              "cap_gib": "17592.2",
              "capalloc": "4632323555328",
              "datatype": "FB 512T",
              "easytier": "managed",
              "id": "A000",
              "lss": "A0",
              "name": "ansible",
              "pool": "P0",
              "real_cap": "4632323555328",
              "state": "normal",
              "stgtype": "fb",
              "tieralloc": [
                {
                  "allocated": "4549091786752",
                  "tier": "SSD"
                },
                {
                  "allocated": "5234491392",
                  "tier": ""
                }
              ],
              "tp": "ese",
              "virtual_cap": "17592186044416"
          }
      ]
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.ds8000.plugins.module_utils.ds8000 import Ds8000ManagerBase, ds8000_argument_spec

# The REST API returns links. pyds8k representation returns as links or with values containing empty strings.
KEYS_TO_DELETE = ['link', 'eserep', 'tserep', 'volumes']


class poolsInformer(Ds8000ManagerBase):
    def pool_info_collector(self):
        pool_by_id = []

        if self.params['id']:
            pool_by_id = self.verify_ds8000_object_exist(self.client.get_pool, pool_id=self.params['id'])
            return self.get_ds8000_objects_from_command_output(pool_by_id)
        else:
            return self.get_ds8000_objects_from_command_output(self.client.get_pools())

    def pool_info(self):
        return self.delete_representation_keys(self.pool_info_collector(), key_list=KEYS_TO_DELETE)


def main():
    argument_spec = ds8000_argument_spec()
    argument_spec.update(id=dict(type='str', aliases=['pool']))

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    pool_informer = poolsInformer(module)

    pools = pool_informer.pool_info()

    module.exit_json(changed=pool_informer.changed, pools=pools)


if __name__ == '__main__':
    main()
