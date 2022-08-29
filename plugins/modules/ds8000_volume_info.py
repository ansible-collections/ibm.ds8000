#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (C) 2021 IBM CORPORATION
# Apache License, Version 2.0 (see https://opensource.org/licenses/Apache-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: ds8000_volume_info
short_description: Return info on DS8000 volumes
description:
  - Return information pertaining to DS8000 volumes.
  - If the optional parameters are not set, information on all volumes on the DS8000 storage system will be returned.
version_added: "1.0.0"
author: Matan Carmeli (@matancarmeli7)
options:
  id:
    description:
        - The volume id.
    type: list
    elements: str
    aliases: [ volume_id ]
  host:
    description:
      - The host that the volumes are mapped to.
    type: str
  pool:
    description:
      - The pool id that the volumes belong to.
    type: str
  lss:
    description:
      - The lss id that the volumes belong to.
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
  elements: dict
  contains:
    id:
      description: The volume ID.
      type: str
      sample: '1000'
    name:
      description: The volume name.
      type: str
      sample: 'ansible'
    state:
      description:  The volume state.
      type: str
      sample: 'normal'
    cap:
      description:  The volume capacity.
      type: int
      sample: 17592186044416
    cap_gb:
      description: The volume capcity in GB.
      type: int
      sample: 16384
    cap_gib:
      description: The volume capacity in GiB.
      type: float
      sample: 17592.2
    real_cap:
      description: The real capacity used by the volume.
      type: int
      sample: 4624471818240
    virtual_cap:
      description: The virtual capacity allocated to the volume.
      type: int
      sample: 17592186044416
    stgtype:
      description: The storage type of the volume.
      type: str
      sample: 'fb'
    VOLSER:
      description: The volume serial number. A volume serial number is 6 bytes of data, displayed as 6 characters.
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
      description: The volume device type and the machine type.
      type: str
      sample: '2107-900'
    datatype:
      description: The volume data type.
      type: str
      sample: 'FB 512T'
    easytier:
      description: The state of management by Easy Tier.
      type: str
      sample: 'managed'
    tieralloc:
      description: A list describing the tier allocation.
      type: list
      elements: dict
      contains:
        allocated:
          description: The capacity allocated to the tier.
          type: int
          sample: 4944866312192
        tier:
          description:  The tier type.
          type: str
          sample: 'SSD'
    lss:
      description: The lss ID the volume belongs to.
      type: str
      sample: 'A0'
    pool:
      description: The pool ID the volume belongs to.
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
            "easytier": "none",
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

# The REST API returns links or even not the key. pyds8k representation returns as links or with values containing empty strings.
REPR_KEYS_TO_DELETE = ['link', 'hosts', 'flashcopy', 'pprc']


class VolumesInformer(Ds8000ManagerBase):
    def volume_info_collector(self):
        volume_by_id = []
        volumes_by_host = []
        volumes_by_pool = []
        volumes_by_lss = []

        if self.params['id']:
            for vol_id in self.params['id']:
                volume_by_id.append(self.verify_ds8000_object_exist(self.client.get_volume, volume_id=vol_id))
        if self.params['host']:
            if self.verify_ds8000_object_exist(self.client.get_host, host_name=self.params['host']):
                volumes_by_host = self.get_ds8000_objects_from_command_output(self.client.get_volumes_by_host(host_name=self.params['host']))
        if self.params['pool']:
            if self.verify_ds8000_object_exist(self.client.get_pool, pool_id=self.params['pool']):
                volumes_by_pool = self.get_ds8000_objects_from_command_output(self.client.get_volumes_by_pool(pool_id=self.params['pool']))
        if self.params['lss']:
            if self.verify_ds8000_object_exist(self.client.get_lss, lss_id=self.params['lss']):
                volumes_by_lss = self.get_ds8000_objects_from_command_output(self.client.get_volumes_by_lss(lss_id=self.params['lss']))

        if volumes_by_host and volumes_by_pool and volumes_by_lss:
            volumes_by_host_and_pool = [volume_dict for volume_dict in volumes_by_host if volume_dict in volumes_by_pool]
            volumes_by_host_and_pool_and_lss = [volume_dict for volume_dict in volumes_by_host_and_pool if volume_dict in volumes_by_lss]
            return volumes_by_host_and_pool_and_lss
        elif volumes_by_host and volumes_by_pool:
            volumes_by_pool_and_host = [volume_dict for volume_dict in volumes_by_host if volume_dict in volumes_by_pool]
            return volumes_by_pool_and_host
        elif volumes_by_pool and volumes_by_lss:
            volumes_by_pool_and_lss = [volume_dict for volume_dict in volumes_by_pool if volume_dict in volumes_by_lss]
            return volumes_by_pool_and_lss
        elif volumes_by_host and volumes_by_lss:
            volumes_by_host_and_lss = [volume_dict for volume_dict in volumes_by_host if volume_dict in volumes_by_lss]
            return volumes_by_host_and_lss
        elif volumes_by_host:
            return volumes_by_host
        elif volumes_by_pool:
            return volumes_by_pool
        elif volumes_by_lss:
            return volumes_by_lss
        elif volume_by_id:
            return self.get_ds8000_objects_from_command_output(volume_by_id)
        else:
            return self.get_all_volumes()

    def volume_info(self):
        return self.delete_representation_keys(self.volume_info_collector(), key_list=REPR_KEYS_TO_DELETE)


def main():
    argument_spec = ds8000_argument_spec()
    argument_spec.update(id=dict(type='list', elements='str', aliases=['volume_id']), host=dict(type='str'), pool=dict(type='str'), lss=dict(type='str'))

    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=[('id', 'host'), ('id', 'pool'), ('id', 'lss')],
        supports_check_mode=True,
    )

    volume_informer = VolumesInformer(module)

    volumes = volume_informer.volume_info()

    module.exit_json(changed=volume_informer.changed, volumes=volumes)


if __name__ == '__main__':
    main()
