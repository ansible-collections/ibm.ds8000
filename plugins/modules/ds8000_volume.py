#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (C) 2021 IBM CORPORATION
# Apache License, Version 2.0 (see https://opensource.org/licenses/Apache-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: ds8000_volume
short_description: Manage DS8000 volumes
description:
  - Manage DS8000 volumes.
version_added: "1.0.0"
author: Matan Carmeli (@matancarmeli7)
options:
  name:
    description:
      - The name of the DS8000 volume to work with.
      - Required when I(state=present)
    type: str
  state:
    description:
      - Specify the state the DS8000 volume should be in.
    type: str
    default: present
    choices:
      - present
      - absent
  id:
    description:
      - The volume IDs of the DS8000 volume to work with.
      - Required when I(state=absent)
      - Only one element is allowed when I(alias=yes)
    type: list
    elements: str
    aliases: [ volume_id ]
  volume_type:
    description:
      - The volume type that will be created.
      - Valid value is fixed block C(fb) or count key data C(ckd).
    choices:
      - fb
      - ckd
    type: str
    default: fb
  capacity:
    description:
      - The size of the volume.
      - Required when I(state=present)
    type: str
  capacity_type:
    description:
      - The units of measurement of the size of the volume.
    choices:
      - gib
      - bytes
      - cyl
      - mod1
    type: str
    default: gib
  lss:
    description:
      - The logical subsystem (lss) that the volume will be created on.
    type: str
  pool:
    description:
      - The pool id that the volume will be created on.
      - Required when I(state=present)
    type: str
  storage_allocation_method:
    description:
      - Choose the storage allocation method that the DS8000 will use in creating your volume.
      - Valid value is C(none), extent space-efficient C(ese), track space-efficient C(tse).  # TODO remove tse?
    choices:
      - none
      - ese
      - tse
    type: str
    default: none
  quantity:
    description:
      - The number of volumes that will be created.
    type: int
    default: 1
  alias:
    description:
      - Boolean specifying if the id is an alias
    type: bool
  alias_order:
    description:
      -  The order in which alias volume IDs are assigned.
    choices:
      - decrement
      - increment
    type: str
    default: decrement
  ckd_base_ids:
    description:
      -  List of existing base CKD volume IDs to create aliases for.
    type: list
    elements: str
notes:
  - Does not support C(check_mode).
  - Is not idempotent.
extends_documentation_fragment:
  - ibm.ds8000.ds8000.documentation
'''

EXAMPLES = r'''
- name: Ensure that a volume exists in the storage
  ibm.ds8000.ds8000_volume:
    hostname: "{{ ds8000_host }}"
    username: "{{ ds8000_username }}"
    password: "{{ ds8000_password }}"
    name: volume_name_test
    state: present
    pool: P1
    capacity: "1"
  register: volume
- debug:
  var: volume.id

- name: Ensure that a volume does not exist in the storage
  ibm.ds8000.ds8000_volume:
    hostname: "{{ ds8000_host }}"
    username: "{{ ds8000_username }}"
    password: "{{ ds8000_password }}"
    id: "FFFF"
    state: absent
'''

RETURN = r'''
volumes:
    description: A list of dictionaries describing the volumes.
    returned: I(state=present) changed
    type: list
    elements: dict
    contains:
      id:
        description: Volume ID.
        type: str
        sample: "1000"
      name:
        description: Volume name.
        type: str
        sample: "ansible"
    sample: |
      [
        {
          "id": "3001",
          "name": "ansible"
        }
      ]
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.text.converters import to_native
from ansible_collections.ibm.ds8000.plugins.module_utils.ds8000 import Ds8000ManagerBase, ds8000_argument_spec, ABSENT, PRESENT

REPR_KEYS_TO_DELETE = ['link', 'hosts', 'flashcopy', 'pprc']


class VolumeManager(Ds8000ManagerBase):
    def volume_present(self):
        if self.params['alias']:
            if len(self.params['id']) != 1:
                self.module.fail_json(msg="Only one id is allowed when creating alias volumes.")

            self._create_alias_volume(self.params['id'][0])
        else:
            self._create_volume()
        return {'changed': self.changed, 'failed': self.failed, 'volumes': self.volume_facts}

    def volume_absent(self):
        # TODO DSANSIBLE-39.  For now, loop calls
        for vol_id in self.params['id']:
            self._delete_volume(vol_id)
        return {'changed': self.changed, 'failed': self.failed}

    def _create_volume(self):
        if self.params['id'] and self.params['quantity'] > 1:
            self.module.fail_json(msg="parameters are mutually exclusive when creating volumes: id|quantity")

        try:
            kwargs = dict(
                name_col=None,  # create_volumes required arg, needs to be set to None to not use
                name=self.params['name'],
                ids=self.params['id'] if self.params['id'] else None,
                cap=self.params['capacity'],
                pool=self.params['pool'],
                stgtype=self.params['volume_type'],
                tp=self.params['storage_allocation_method'],
                captype=self.params['capacity_type'],
                lss=self.params['lss'],
                quantity=self.params['quantity'],
            )
            volumes = []
            volumes = self.client.create_volumes(**kwargs)
            self.check_multi_response_results(volumes, item_list=self.params['id'] if self.params['id'] else None, item_name='id')
            self.volume_facts = self.delete_representation_keys(self.get_ds8000_objects_from_command_output(volumes), key_list=REPR_KEYS_TO_DELETE)
            self.changed = True
        except Exception as generic_exc:
            self.failed = True
            self.module.fail_json(msg="Failed to create volume on the DS8000 storage system. ERR: {error}".format(error=to_native(generic_exc)))

    def _create_alias_volume(self, volume_id):
        try:
            kwargs = dict(
                id=volume_id,
                ckd_base_ids=self.params['ckd_base_ids'],
                quantity=self.params['quantity'],
                alias_create_order=self.params['alias_order'],
            )
            volumes = []
            volumes = self.client.create_alias_volumes(**kwargs)

            # Handle multi response unknown id by building the list of ids that would be used
            total_qty = len(self.params['ckd_base_ids']) * self.params['quantity']
            alias_ids = []
            if self.params['alias_order'] == 'increment':
                for i in range(total_qty):
                    alias_ids.append('%x' % (int(volume_id, 16) + i))
            else:
                for i in reversed(range(total_qty)):
                    alias_ids.append('%x' % (int(volume_id, 16) - i))

            self.check_multi_response_results(volumes, item_list=alias_ids, item_name='id')
            self.volume_facts = self.delete_representation_keys(self.get_ds8000_objects_from_command_output(volumes), key_list=REPR_KEYS_TO_DELETE)
            self.changed = True
        except Exception as generic_exc:
            self.failed = True
            self.module.fail_json(msg="Failed to create volume on the DS8000 storage system. ERR: {error}".format(error=to_native(generic_exc)))

    def _delete_volume(self, volume_id):
        try:
            self.client.delete_volume(volume_id)
            self.changed = True
        except Exception as generic_exc:
            self.failed = True
            self.module.fail_json(
                msg="Failed to delete the volume {volume_id} from the DS8000 storage system. "
                "ERR: {error}".format(volume_id=volume_id, error=to_native(generic_exc))
            )


def main():
    argument_spec = ds8000_argument_spec()
    argument_spec.update(
        name=dict(type='str'),
        state=dict(type='str', default=PRESENT, choices=[ABSENT, PRESENT]),
        volume_type=dict(type='str', default='fb', choices=['fb', 'ckd']),  # TODO change to stg_type?
        pool=dict(type='str'),
        capacity=dict(type='str'),
        capacity_type=dict(type='str', default='gib', choices=['gib', 'bytes', 'cyl', 'mod1']),
        lss=dict(type='str'),
        storage_allocation_method=dict(type='str', default='none', choices=['none', 'ese', 'tse']),
        id=dict(type='list', elements='str', aliases=['volume_id']),
        alias=dict(type='bool'),
        alias_order=dict(type='str', default='decrement', choices=['decrement', 'increment']),
        ckd_base_ids=dict(type='list', elements='str'),
        quantity=dict(type='int', default=1),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_if=[
            ['state', PRESENT, ('name', 'alias'), True],
            ['state', ABSENT, ('id',)],
        ],
        required_by={'alias': ('ckd_base_ids', 'id'), 'name': ('capacity', 'pool')},
        mutually_exclusive=[
            ['alias', 'name'],
            ['alias', 'volume_type'],
            ['alias', 'pool'],
            ['alias', 'capacity'],
            ['alias', 'capacity_type'],
            ['alias', 'lss'],
            ['alias', 'storage_allocation_method'],
        ],
        supports_check_mode=False,
    )

    volume_manager = VolumeManager(module)

    if module.params['state'] == PRESENT:
        result = volume_manager.volume_present()
    elif module.params['state'] == ABSENT:
        result = volume_manager.volume_absent()

    if result['failed']:
        module.fail_json(**result)
    else:
        module.exit_json(**result)


if __name__ == '__main__':
    main()
