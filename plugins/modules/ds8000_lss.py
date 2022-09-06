#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2022 IBM CORPORATION
# Apache License, Version 2.0 (see https://opensource.org/licenses/Apache-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: ds8000_lss
short_description: Manage DS8000 lsses
description:
  - Manage a DS8000 storage image logical subsystem (lss), also known as a logical control unit (lcu).
  - A lcu is configured to represent a grouping of logical CKD volumes.
  - The DS8000 has a 64 KB 256 volume address space that is partitioned into 255 lss units,
    where each lss contains 256 logical volume numbers. The 255 lss units are assigned to one of 16 address groups,
    where each address group contains 16 lsses, or 4 KB volume addresses.
  - lcus are typically created in groups of 16, beginning at lss address 00.
version_added: "1.1.0"
author: NjM3MjY5NzAgNzA3MzA3 (@NjM3MjY5NzAgNzA3MzA3)
options:
  id:
    description:
      - The lss ID to be created.
      - An lss ID is two hexadecimal characters 00 - FE.
    required: true
    type: str
    aliases: [ lss ]
  state:
    description:
    - Specify the state the DS8000 lss should be in.
    type: str
    default: present
    choices:
      - present
      - absent
  ssid:
    description:
      - The subsystem ID that you assign.
      - A subsystem ID is four hexadecimal characters 0000-FFFF.
      - Required when I(state=present)
    type: str
  ckd_type:
    description:
      - The type of lss to create.
    type: str
    default: 3990-6
    choices:
      - 3990-3
      - 3990-tpf
      - 3990-6
      - bs2000
notes:
  - Supports C(check_mode).
extends_documentation_fragment:
  - ibm.ds8000.ds8000.documentation
'''

EXAMPLES = r'''
- name: Ensure that a lss exists
  ibm.ds8000.ds8000_lss:
    hostname: "{{ ds8000_host }}"
    username: "{{ ds8000_username }}"
    password: "{{ ds8000_password }}"
    lss_id: "80"
    state: present
    ssid: 2300

- name: Ensure that a lss does not exist
  ibm.ds8000.ds8000_lss:
    hostname: "{{ ds8000_host }}"
    username: "{{ ds8000_username }}"
    password: "{{ ds8000_password }}"
    lss_id: "80"
    state: absent
'''

RETURN = r'''
lss:
    description: A list of dictionaries describing the lsses.
    returned: I(state=present) changed
    type: list
    elements: dict
    contains:
      id:
        description: The lss ID.
        type: str
        sample: "1F"
    sample: |
      [
        {
          "id": "1F"
        }
      ]
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.text.converters import to_native
from ansible_collections.ibm.ds8000.plugins.module_utils.ds8000 import Ds8000ManagerBase, ds8000_argument_spec, ABSENT, PRESENT

LSS_TYPE = 'ckd'
CKD_BASE_CU_TYPES = ['3990-3', '3990-tpf', '3990-6', 'bs2000']
# The REST API returns links. pyds8k representation returns as links or with values containing empty strings.
REPR_KEYS_TO_DELETE = ['link', 'volumes', 'sub_system_identifier']


class LssManager(Ds8000ManagerBase):
    def lss_present(self):
        self.lss_info = []
        self.verify_lss()
        return {'changed': self.changed, 'failed': self.failed, 'lss': self.lss_info}

    def lss_absent(self):
        if self._does_lss_exist():
            self._delete_lss()

        return {'changed': self.changed, 'failed': self.failed}

    def verify_lss(self):
        existing_lss_object = self._does_lss_exist()
        if not existing_lss_object:
            self._create_lss()
        else:
            if existing_lss_object.type != LSS_TYPE:
                self.failed = True
                generic_exc = "lss exists but is not the type {r_type} ({type}).".format(r_type=LSS_TYPE, type=existing_lss_object.type)
                self.module.fail_json(msg="Failed to create lss on DS8000 storage. " "ERR: {error}".format(error=to_native(generic_exc)))

            if existing_lss_object.sub_system_identifier != self.params['ssid'] or existing_lss_object.ckd_base_cu_type != self.params['ckd_type']:
                # If change gets supported
                # if not self.module.check_mode:
                #     self.change_lss()

                self.failed = True
                generic_exc = "lss exists but is not the requested ssid {r_ssid} ({ssid}) or cu_type {r_type} ({type}).".format(
                    r_ssid=self.params['ssid'],
                    ssid=existing_lss_object.sub_system_identifier,
                    r_type=self.params['ckd_type'],
                    type=existing_lss_object.ckd_base_cu_type,
                )
                self.module.fail_json(msg="Failed to create lss on DS8000 storage. " "ERR: {error}".format(error=to_native(generic_exc)))

    def _create_lss(self):
        try:
            kwargs = dict(lss_id=self.params['id'], lcu_type=self.params['ckd_type'], ss_id=self.params['ssid'])
            lss = []
            if not self.module.check_mode:
                lss = self.client.create_lss_ckd(**kwargs)
            self.lss_info = self.delete_representation_keys(self.get_ds8000_objects_from_command_output(lss), key_list=REPR_KEYS_TO_DELETE)
            self.changed = True
        except Exception as generic_exc:
            self.failed = True
            self.module.fail_json(msg="Failed to create lss on DS8000 storage. " "ERR: {error}".format(error=to_native(generic_exc)))

    # def _change_lss(self):
    #     try:
    #         kwargs = dict(
    #             lss_id=self.params['id'],
    #             ssid=self.params['ssid'],
    #             ckd_type=self.params['ckd_type'],
    #         )
    #         self.client.update_lss_ckd(**kwargs)
    #         self.changed = True
    #     except Exception as generic_exc:
    #         self.failed = True
    #         self.module.fail_json(msg="Failed to change lss on DS8000 storage. " "ERR: {error}".format(error=to_native(generic_exc)))

    def _delete_lss(self):
        try:
            if not self.module.check_mode:
                self.client.delete_lss_by_id(self.params['id'])
            self.changed = True
        except Exception as generic_exc:
            self.failed = True
            self.module.fail_json(
                msg="Failed to delete the lss {id} from DS8000 storage. " "ERR: {error}".format(id=self.params['id'], error=to_native(generic_exc))
            )

    def _does_lss_exist(self):
        return self.does_ds8000_object_exist(self.client.get_lss_by_id, lss_id=self.params['id'])


def main():
    argument_spec = ds8000_argument_spec()
    argument_spec.update(
        id=dict(type='str', aliases=['lss'], required=True),
        state=dict(type='str', default=PRESENT, choices=[ABSENT, PRESENT]),
        ssid=dict(type='str'),
        ckd_type=dict(type='str', default='3990-6', choices=CKD_BASE_CU_TYPES),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_if=[
            ['state', PRESENT, ('ssid',)],
        ],
        supports_check_mode=True,
    )

    lss_manager = LssManager(module)

    if module.params['state'] == PRESENT:
        result = lss_manager.lss_present()
    elif module.params['state'] == ABSENT:
        result = lss_manager.lss_absent()

    if result['failed']:
        module.fail_json(**result)
    else:
        module.exit_json(**result)


if __name__ == '__main__':
    main()
