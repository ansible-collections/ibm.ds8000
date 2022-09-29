#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (C) 2022 IBM CORPORATION
# Apache License, Version 2.0 (see https://opensource.org/licenses/Apache-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: ds8000_marray_info
short_description: Return info on DS8000 managed arrays
description:
  - Return information pertaining to DS8000 managed arrays.
  - If the optional parameters are not set, information on all managed arrays on the DS8000 storage system will be returned.
version_added: "1.1.0"
author: NjM3MjY5NzAgNzA3MzA3 (@NjM3MjY5NzAgNzA3MzA3)
options:
  id:
    description:
        - The marray id.
    type: str
    aliases: [ marray ]
notes:
  - Supports C(check_mode).
extends_documentation_fragment:
  - ibm.ds8000.ds8000.documentation
'''

EXAMPLES = r'''
- name: get all the marrays under host
  ibm.ds8000.ds8000_marray_info:
    hostname: "{{ ds8000_host }}"
    username: "{{ ds8000_username }}"
    password: "{{ ds8000_password }}"
    id: MA1

- name: get all the marrays
  ibm.ds8000.ds8000_marray_info:
    hostname: "{{ ds8000_host }}"
    username: "{{ ds8000_username }}"
    password: "{{ ds8000_password }}"
'''

RETURN = r'''
marrays:
  description: A list of dictionaries describing the marrays.
  returned: success
  type: list
  elements: dict
  contains:
    id:
      description: The managed array ID.
      type: str
      sample: 'MA1'
    disk_class:
      description: The class of disks that are members of the array.
      type: str
      sample: ''
    pool:
      description: The pool the managed array belongs to.
      type: str
      sample: 'P0'
  sample: |
    [
        {
            "id": "MA1",
            "disk_class": "",
            "pool": "P0"
        }
    ]
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.ds8000.plugins.module_utils.ds8000 import Ds8000ManagerBase, ds8000_argument_spec

# The REST API returns links. pyds8k representation returns as links or with values containing empty strings.
KEYS_TO_DELETE = ['link']


class marraysInformer(Ds8000ManagerBase):
    def marray_info_collector(self):
        marray_by_id = []

        if self.params['id']:
            marray_by_id = self.verify_ds8000_object_exist(self.client.get_marray, marray_id=self.params['id'])
            return self.get_ds8000_objects_from_command_output(marray_by_id)
        else:
            return self.get_ds8000_objects_from_command_output(self.client.get_marrays())

    def marray_info(self):
        return self.delete_representation_keys(self.marray_info_collector(), key_list=KEYS_TO_DELETE)


def main():
    argument_spec = ds8000_argument_spec()
    argument_spec.update(id=dict(type='str', aliases=['marray']))

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    marray_informer = marraysInformer(module)

    marrays = marray_informer.marray_info()

    module.exit_json(changed=marray_informer.changed, marrays=marrays)


if __name__ == '__main__':
    main()
