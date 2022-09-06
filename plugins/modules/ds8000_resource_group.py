#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (C) 2022 IBM CORPORATION
# Apache License, Version 2.0 (see https://opensource.org/licenses/Apache-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: ds8000_resource_group
short_description: Manage DS8000 resource groups
description:
  - Manage DS8000 resource groups.
version_added: "1.1.0"
author: NjM3MjY5NzAgNzA3MzA3 (@NjM3MjY5NzAgNzA3MzA3)
options:
  label:
    description:
      - The resource group label is 1 to 32 characters and is limited to upper and lower case alphabetic and numeric characters,
        and the special characters (-), (_), and (.).
      - Required when I(state=present)
    type: str
  state:
    description:
      - Specify the state the DS8000 resource group should be in.
    type: str
    default: present
    choices:
      - present
      - absent
  name:
    description:
      - The nickname that you assigned for this resource group object.
    type: str
  id:
    description:
      - Unique identifier that is assigned to this resource group ID in the form RG
      - If not specified, one will be chosen.
      - Resource Group 0 is predefined and cannot be created, deleted, or modified. By default, all resources belong to this group unless otherwise specified.
    type: str
  cs_global:
    description:
      - All of the Copy Services requests that establish or re-establish a relationship,
        and are subject to this resource scope including FlashCopy and PPRC relationships.
    type: str
  pass_global:
    description:
      - All of the Copy Services requests that are issued though a pass-through logical volume are treated as a relationship
        between the pass-through logical volume and source logical volume and are subject to this resource scope.
    type: str
  gm_masters:
    description:
      - An array of Global Mirror session IDs that are allowed to be used as a master session for volumes in this resource.
      - A Session ID is a hexadecimal number in the 01 - FF range.
    type: list
    elements: str
  gm_sessions:
    description:
      - An array of Global Mirror session IDs that are allowed to be used for the volumes in this resource.
      - A Session ID is a hexadecimal number in the 01 - FF range.
    type: list
    elements: str
notes:
  - Supports C(check_mode).
extends_documentation_fragment:
  - ibm.ds8000.ds8000.documentation
'''

EXAMPLES = r'''
- name: Ensure that a resource exists in the storage
  ibm.ds8000.ds8000_resource_group:
    hostname: "{{ ds8000_host }}"
    username: "{{ ds8000_username }}"
    password: "{{ ds8000_password }}"
    label: my_rg
    state: present
    cs_global: '00'

- name: Ensure that a resource group does not exist in the storage
  ibm.ds8000.ds8000_resource_group:
    hostname: "{{ ds8000_host }}"
    username: "{{ ds8000_username }}"
    password: "{{ ds8000_password }}"
    label: my_rg
    state: absent
'''

RETURN = r'''
resource_groups:
    description: A list of dictionaries describing the resource groups.
    returned: I(state=present) changed
    type: list
    elements: dict
    contains:
      id:
        description: The Resource Group ID.
        type: str
        sample: "RG1"
    sample: |
      [
        {
          "id": "RG0"
        }
      ]
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.text.converters import to_native
from ansible_collections.ibm.ds8000.plugins.module_utils.ds8000 import Ds8000ManagerBase, ds8000_argument_spec, ABSENT, PRESENT

# The REST API returns links. pyds8k representation returns as links or with values containing empty strings.
REPR_KEYS_TO_DELETE = ['link', 'name', 'label']


class ResourceGroupManager(Ds8000ManagerBase):
    def resource_group_present(self):
        self.resource_group_info = []
        self._verify_resource_group()
        return {'changed': self.changed, 'failed': self.failed, 'resource_groups': self.resource_group_info}

    def resource_group_absent(self):
        self._delete_resource_group()
        return {'changed': self.changed, 'failed': self.failed}

    def _verify_resource_group(self):
        existing_resource_group_object = self._does_resource_group_exist()
        if not existing_resource_group_object:
            self._create_resource_group()
            # Create only accepts label and name.  If any of the other parameters are provided, run a change after the create to set them also.
            change_params_dict = dict(
                cs_global=self.params['cs_global'],
                pass_global=self.params['pass_global'],
                gm_masters=self.params['gm_masters'],
                gm_sessions=self.params['gm_sessions'],
            )
            if any(change_params_dict.values()):
                self._change_resource_group(change_params_dict)
        else:
            # Create a dict of the existing object values to compare to specified parameters
            existing_resource_group_dict = dict(
                label=existing_resource_group_object.label,
                name=existing_resource_group_object.name,
                cs_global=existing_resource_group_object.name,
                pass_global=existing_resource_group_object.pass_global,
                gm_masters=existing_resource_group_object.gm_masters,
                gm_sessions=existing_resource_group_object.gm_sessions,
            )

            params_dict = dict(
                label=self.params['label'],
                name=self.params['name'],
                cs_global=self.params['cs_global'],
                pass_global=self.params['pass_global'],
                gm_masters=self.params['gm_masters'],
                gm_sessions=self.params['gm_sessions'],
            )

            if params_dict != existing_resource_group_dict:
                self._change_resource_group(params_dict)

    def _create_resource_group(self):
        if not self.params['label']:
            self.failed = True
            generic_exc = "label is required when creating a resource group"
            self.module.fail_json(msg="Failed to create resource group on DS8000 storage. " "ERR: {error}".format(error=to_native(generic_exc)))

        try:
            param_args = dict(
                label=self.params['label'],
                name=self.params['name'],
                resource_group_id=self.params['id'],
            )
            resource_group = []
            if not self.module.check_mode:
                resource_group = self.client.create_resource_group(**param_args)
                # set id in the params dict to the created id in case a change needs to be run to update optional fields
                # TODO is this ok, or should I save in a class variable?
                self.params['id'] = resource_group[0].id
                self.resource_group_info = self.delete_representation_keys(
                    self.get_ds8000_objects_from_command_output(resource_group), key_list=REPR_KEYS_TO_DELETE
                )
            self.changed = True
        except Exception as generic_exc:
            self.failed = True
            self.module.fail_json(
                msg="Failed to create the resource group {label} on the DS8000 storage. ERR: {error}".format(
                    label=self.params['label'], error=to_native(generic_exc)
                )
            )

    def _change_resource_group(self, param_args):
        try:
            if not self.module.check_mode:
                self.client.update_resource_group(self.params['id'], **param_args)
                # change_resource_group only returns a success dict
                # the module returns id on changed, so build the list
                self.resource_group_info.append({'id': self.params['id']})
                # query the resource group to get the actual values
                # self.resource_group_info = self.delete_representation_keys(
                #     self.get_ds8000_objects_from_command_output(self.client.get_resource_group(self.params['id'])), key_list=REPR_KEYS_TO_DELETE
                # )
            self.changed = True
        except Exception as generic_exc:
            self.failed = True
            self.module.fail_json(msg="Failed to change resource group on DS8000 storage. " "ERR: {error}".format(error=to_native(generic_exc)))

    def _delete_resource_group(self):
        resource_group = self._does_resource_group_exist()
        if resource_group:
            try:
                if not self.module.check_mode:
                    self.client.delete_resource_group(resource_group.id)
                self.changed = True
            except Exception as generic_exc:
                self.failed = True
                self.module.fail_json(
                    msg="Failed to delete the resource group {rg_id} from the DS8000 storage. ERR: {error}".format(
                        rg_id=resource_group.id, error=to_native(generic_exc)
                    )
                )

    def _does_resource_group_exist(self):
        if self.params['id']:
            return self.verify_ds8000_object_exist(self.client.get_resource_group, self.params['id'])

        return self.get_resource_group_from_label(self.params['label'])


def main():
    argument_spec = ds8000_argument_spec()
    argument_spec.update(
        label=dict(type='str'),
        state=dict(type='str', default=PRESENT, choices=[ABSENT, PRESENT]),
        id=dict(type='str'),
        name=dict(type='str'),
        cs_global=dict(type='str'),
        pass_global=dict(type='str', no_log=False),
        gm_masters=dict(type='list', elements='str'),
        gm_sessions=dict(type='list', elements='str'),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    resource_group = ResourceGroupManager(module)

    if module.params['state'] == PRESENT:
        result = resource_group.resource_group_present()
    elif module.params['state'] == ABSENT:
        result = resource_group.resource_group_absent()

    if result['failed']:
        module.fail_json(**result)
    else:
        module.exit_json(**result)


if __name__ == '__main__':
    main()
