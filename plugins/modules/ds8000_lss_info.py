#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (C) 2022 IBM CORPORATION
# Apache License, Version 2.0 (see https://opensource.org/licenses/Apache-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: ds8000_lss_info
short_description: Return info on DS8000 lsses
description:
  - Return information pertaining to DS8000 lsses.
  - If the optional parameters are not set, information on all lsses on the DS8000 storage system will be returned.
version_added: "1.1.0"
author: NjM3MjY5NzAgNzA3MzA3 (@NjM3MjY5NzAgNzA3MzA3)
options:
  id:
    description:
      - The logical subsystem (lss) ID to be queried.
      - An lss ID is two hexadecimal characters 00 - FE.
    type: str
    aliases: [ lss ]
  lss_type:
    description:
      - The lss type to query
    choices:
      - fb
      - ckd
    type: str
    default: ckd
notes:
  - Supports C(check_mode).
extends_documentation_fragment:
  - ibm.ds8000.ds8000.documentation
'''

EXAMPLES = r'''
- name: get all the lsses
  ibm.ds8000.ds8000_lss_info:
    hostname: "{{ ds8000_host }}"
    username: "{{ ds8000_username }}"
    password: "{{ ds8000_password }}"

- name: get all the ckd lsses
  ibm.ds8000.ds8000_lss_info:
    hostname: "{{ ds8000_host }}"
    username: "{{ ds8000_username }}"
    password: "{{ ds8000_password }}"
    lss_type: ckd

- name: get lss 00
  ibm.ds8000.ds8000_lss_info:
    hostname: "{{ ds8000_host }}"
    username: "{{ ds8000_username }}"
    password: "{{ ds8000_password }}"
    id: '00'
'''

RETURN = r'''
lss:
  description: A list of dictionaries describing the lsses.
  returned: success
  type: list
  elements: dict
  contains:
    id:
      description:
        - The unique identifier assigned to the logical subsystem (lss) or logical control unit object (lcu).
        - It includes the storage image ID and the 2 digit lss ID 00 - FE.
      type: str
      sample: '00'
    addrgrp:
      description: The address group object the lss is a member of.
      type: int
      sample: 0
    cc_session_timeout:
      description: The assigned concurrent copy session timeout value.
      type: int
      sample: 300
    ckd_base_cu_type:
      description: The lss type you designated for the lcu.
      type: str
      sample: '3990-6'
    configvols:
      description:
        - The number of volumes or the logical devices assigned to the lss.
        - This number includes base count key data (ckd) volumes and alias ckd volumes.
      type: str
      sample: '256'
    critical_mode:
      description: Indicates whether the critical heavy mode for Remote Mirror and Copy operations is in effect.
      type: str
      sample: 'disabled'
    extended_long_busy_time:
      description: The assigned extended long busy timeout value.
      type: int
      sample: 120
    group:
      description:
        - The server that manages the lcu group.
        - The displayed values are 0 or 1.
      type: int
      sample: 0
    pprc_consistency_group:
      description: The assigned PPRC consistency group state setting.
      type: str
      sample: 'disabled'
    sub_system_identifier:
      description:
        - The subsystem ID that you assigned to this lcu.
        - The range of values that you selected from is 0001 - FFFF.
      type: str
      sample: '0D58'
    type:
      description:
        - The type of storage volumes contained by this lss.
        - The value displayed is fb (fixed block) or ckd (count key data)
      type: str
      sample: 'ckd'
    xrc_session_timeout:
      description: The assigned XRC session timeout value.
      type: int
      sample: 300
  sample: |
    [
        {
            "addrgrp": "0",
            "cc_session_timeout": "300",
            "ckd_base_cu_type": "3990-6",
            "configvols": "256",
            "critical_mode": "disabled",
            "extended_long_busy_time": "120",
            "group": "0",
            "id": "00",
            "pprc_consistency_group": "disabled",
            "sub_system_identifier": "5031",
            "type": "ckd",
            "xrc_session_timeout": "300"
        }
    ]
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.ds8000.plugins.module_utils.ds8000 import Ds8000ManagerBase, ds8000_argument_spec

# The REST API returns links. pyds8k representation returns as links or with values containing empty strings.
KEYS_TO_DELETE = ['link', 'volumes']


class lssInformer(Ds8000ManagerBase):
    def lss_info_collector(self):
        lss_by_id = []
        lss_by_type = []

        if self.params['id']:
            lss_by_id = self.verify_ds8000_object_exist(self.client.get_lss, lss_id=self.params['id'])
            return self.get_ds8000_objects_from_command_output(lss_by_id)
        elif self.params['lss_type']:
            lss_by_type = self.verify_ds8000_object_exist(self.client.get_lss, lss_type=self.params['lss_type'])
            return self.get_ds8000_objects_from_command_output(lss_by_type)
        else:
            return self.get_ds8000_objects_from_command_output(self.client.get_lss())

    def lss_info(self):
        return self.delete_representation_keys(self.lss_info_collector(), key_list=KEYS_TO_DELETE)


def main():
    argument_spec = ds8000_argument_spec()
    argument_spec.update(id=dict(type='str', aliases=['lss']), lss_type=dict(type='str', default='ckd', choices=['fb', 'ckd']))

    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=[('id', 'lss_type')],  # TODO change to stg_type?
        supports_check_mode=True,
    )

    lss_informer = lssInformer(module)

    lss = lss_informer.lss_info()

    module.exit_json(changed=lss_informer.changed, lss=lss)


if __name__ == '__main__':
    main()
