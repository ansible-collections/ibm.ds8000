#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2021, Matan Carmeli <matan.carmeli7@gmail.com>
# GNU General Public License v3.0+ (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
author: Matan Carmeli (@matancarmeli7)
module: ds8000_volume
short_description: Manage DS8000 volumes.
description:
  - Manage DS8000 volumes.
options:
  name:
    description:
      - The name of the DS8000 volume to work with.
    type: str
  state:
    description:
    - Specify the state the DS8000 volume should be in.
    type: str
    default: present
    choices:
      - present
      - absent
  volume_id:
    description:
      - The volume ID of the DS8000 volume to work with.
    type: str
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
      - The pool that the volume will create on.
    type: str
  storage_allocation_method:
    description:
      - Choose the storage allocation method that the DS8000 will use in creating your volume.
      - Valid value is C(none), extent space-efficient C(ese), track space-efficient C(tse).
    choices:
      - none
      - ese
      - tse
    type: str
    default: none
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
    capacity: '1'

- name: Ensure that a volume does not exist in the storage
  ibm.ds8000.ds8000_volume:
    hostname: "{{ ds8000_host }}"
    username: "{{ ds8000_username }}"
    password: "{{ ds8000_password }}"
    name: volume_name_test
    state: absent
'''

RETURN = r''' # '''

import json
from ansible_collections.ibm.ds8000.plugins.module_utils.ds8000 import (
    PyDs8k, ds8000_argument_spec, ABSENT, PRESENT)
from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule

class VolumeManager(PyDs8k):

    def ds8000_volume_present(self):
        self._create_ds8000_volume()
        return {'changed': self.changed, 'failed': self.failed}

    def _create_ds8000_volume(self):
        volume_type = self.params['volume_type']
        try:
            if volume_type == 'fb':
                self.client.create_volume_fb(
                    name=self.params['name'],
                    cap=self.params['capacity'],
                    pool=self.params['pool'],
                    tp=self.params['storage_allocation_method'],
                    captype=self.params['capacity_type'],
                    lss=self.params['lss'])
            elif volume_type == 'ckd':
                self.client.create_volume_ckd(
                    name=self.params['name'],
                    cap=self.params['capacity'],
                    pool=self.params['pool'],
                    tp=self.params['storage_allocation_method'],
                    captype=self.params['capacity_type'],
                    lss=self.params['lss'])
            self.changed = True
        except Exception as generic_exc:
            self.failed = True
            self.module.fail_json(
                msg="Failed to create volume on DS8000 storage. "
                "ERR: {error}".format(
                    error=to_native(generic_exc)))

    def ds8000_volume_absent(self, volume_name='', volume_id=''):
        if volume_name:
            volume_ids = self.get_volume_ids_from_name(volume_name)
            for volume_id in volume_ids:
                self._delete_ds8000_volume(
                    volume_id, volume_name)
        elif volume_id:
            volume_name = self._get_volume_name(volume_id)
            if volume_name:
                self._delete_ds8000_volume(
                    volume_id, volume_name)
        return {'changed': self.changed, 'failed': self.failed}

    def _get_volume_name(self, volume_id):
        volumes = self.get_all_volumes_in_ds8000_storage()
        for volume in volumes:
            if volume['id'] == volume_id:
                return volume['name']
        return None

    def _delete_ds8000_volume(self, volume_id, volume_name):
        try:
            self.client.delete_volume(volume_id)
            self.changed = True
        except Exception as generic_exc:
            self.failed = True
            self.module.fail_json(
                msg="Failed to delete the volume {volume_name} from DS8000 storage. "
                "ERR: {error}".format(
                    volume_name=volume_name,
                    error=to_native(generic_exc)))


def main():
    argument_spec = ds8000_argument_spec()
    argument_spec.update(
        name=dict(type='str'),
        state=dict(type='str', default=PRESENT, choices=[
            ABSENT, PRESENT]),
        volume_type=dict(type='str', default='fb', choices=[
            'fb', 'ckd']),
        pool=dict(type='str'),
        capacity=dict(type='str'),
        capacity_type=dict(type='str', default='gib', choices=[
            'gib', 'bytes', 'cyl', 'mod1']),
        lss=dict(type='str'),
        storage_allocation_method=dict(type='str', default='none', choices=[
            'none', 'ese', 'tse']),
        volume_id=dict(type='str'))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=[
            ['name', 'volume_id'],
        ],
    )

    pyds8kh = VolumeManager(module)

    if module.params['state'] == PRESENT:
        result = pyds8kh.ds8000_volume_present()
    elif module.params['state'] == ABSENT:
        if module.params.get('volume_id'):
            result = pyds8kh.ds8000_volume_absent(
                volume_id=module.params['volume_id'])
        elif module.params.get('name'):
            result = pyds8kh.ds8000_volume_absent(module.params['name'])

    if result['failed']:
        module.fail_json(**result)
    else:
        module.exit_json(**result)


if __name__ == '__main__':
    main()
