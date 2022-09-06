#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (C) 2022 IBM CORPORATION
# Apache License, Version 2.0 (see https://opensource.org/licenses/Apache-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: ds8000_resource_group_info
short_description: Return info on DS8000 resource groups
description:
  - Return info on DS8000 resource groups.
version_added: "1.1.0"
author: NjM3MjY5NzAgNzA3MzA3 (@NjM3MjY5NzAgNzA3MzA3)
options:
  id:
    description:
      - The unique identifier that is assigned to this resource group ID in the form RG\#.
    type: str
  label:
    description:
      - The resource group label.
    type: str
notes:
  - Supports C(check_mode).
extends_documentation_fragment:
  - ibm.ds8000.ds8000.documentation
'''

EXAMPLES = r'''
- name: get all the resource groups
  ibm.ds8000.ds8000_resource_group_info:
    hostname: "{{ ds8000_host }}"
    username: "{{ ds8000_username }}"
    password: "{{ ds8000_password }}"

- name: get a resource group by label
  ibm.ds8000.ds8000_resource_group_info:
    hostname: "{{ ds8000_host }}"
    username: "{{ ds8000_username }}"
    password: "{{ ds8000_password }}"
    label: my_rg

- name: get a resource group by id
  ibm.ds8000.ds8000_resource_group_info:
    hostname: "{{ ds8000_host }}"
    username: "{{ ds8000_username }}"
    password: "{{ ds8000_password }}"
    id: RG1
'''

RETURN = r'''
resource_groups:
    description: A list of dictionaries describing the resource groups.
    returned: success
    type: list
    elements: dict
    contains:
      id:
        description: The Resource Group ID.
        type: str
        sample: "RG1"
      name:
        description: The Resource Group name.
        type: str
        sample: "ansible"
      state:
        description: The Resource Group state.
        type: str
        sample: "normal"
      label:
        description: The Resource Group label.
        type: str
        sample: "ansible"
      cs_global:
        description:
          - All of the Copy Services requests that establish or re-establish a relationship,
            and are subject to this resource scope including FlashCopy and PPRC relationships.
        type: str
        sample: "public"
      pass_global:
        description:
          - All of the Copy Services requests that are issued though a pass-through logical volume are treated as a relationship
            between the pass-through logical volume and source logical volume and are subject to this resource scope.
        type: str
        sample: "public"
      gm_masters:
        description:
          - An array of Global Mirror session IDs that are allowed to be used as a master session for volumes in this resource.
          - A Session ID is a hexadecimal number in the 01 - FF range.
        type: list
        elements: str
        sample: ["EA", "F0"]
      gm_sessions:
        description:
          - An array of Global Mirror session IDs that are allowed to be used for the volumes in this resource.
          - A Session ID is a hexadecimal number in the 01 - FF range.
        type: list
        elements: str
        sample: ["BE", "FE"]
    sample: |
      [
        {
          "id": "RG0",
          "name": "Default_Resource_Group",
          "state": "normal",
          "label": "PUBLIC",
          "cs_global": "PUBLIC",
          "pass_global": "PUBLIC",
          "gm_masters": ["00", "01", "FE", "FF"],
          "gm_sessions": ["00", "01", "FE", "FF"]
        }
      ]
'''


REPR_KEYS_TO_DELETE = ['link']

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.ds8000.plugins.module_utils.ds8000 import Ds8000ManagerBase, ds8000_argument_spec


class ResourceGroupInformer(Ds8000ManagerBase):
    def resource_group_info_collector(self):
        if self.params['id']:
            return self.get_ds8000_objects_from_command_output(self.verify_ds8000_object_exist(self.client.get_resource_group, self.params['id']))
        if self.params['label']:
            return self.get_ds8000_objects_from_command_output(self.get_resource_group_from_label(self.params['label']))

        return self.get_ds8000_objects_from_command_output(self.client.get_resource_groups())

    def resource_group_info(self):
        if not self.module.check_mode:
            return self.delete_representation_keys(self.resource_group_info_collector(), key_list=REPR_KEYS_TO_DELETE)

        return {}


def main():
    argument_spec = ds8000_argument_spec()
    argument_spec.update(
        id=dict(type='str'),
        label=dict(type='str'),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=[['id', 'label']],
        supports_check_mode=True,
    )

    resource_group_informer = ResourceGroupInformer(module)

    resource_groups = resource_group_informer.resource_group_info()

    module.exit_json(changed=resource_group_informer.changed, resource_groups=resource_groups)


if __name__ == '__main__':
    main()
