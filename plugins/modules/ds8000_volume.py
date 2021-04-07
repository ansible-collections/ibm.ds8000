#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2021, Matan Carmeli <matan.carmeli7@gmail.com>
# GNU General Public License v3.0+ (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
from ..module_utils.ds8000 import (PyDs8k, costume_get_request,
                                   ds8000_argument_spec)
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import json

__metaclass__ = type

DOCUMENTATION = r'''
---
author: Matan Carmeli (@matancarmeli7)
module: ibm.ds8000.ds8000_volume
short_description: Manage DS8000 volumes.
description:
  - Manage DS8000 volumes.
options:
  name:
    description:
      - The Name of the DS8000 volume to work with.
    type: str
  state:
      description:
      - If the module will ensure the volume will be presented on the DS8000 storage or not.
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
- name: Ensure that a volume is exists on the storage
  ibm.ds8000.ds8000_volume:
    hostname: "{{ ds8000_host }}"
    username: "{{ ds8000_username }}"
    password: "{{ ds8000_password }}"
    name: volume_name_test
    state: present
    pool: P1
    capacity: '1'

- name: Ensure that a volume does not exists on the storage
  ibm.ds8000.ds8000_volume:
    hostname: "{{ ds8000_host }}"
    username: "{{ ds8000_username }}"
    password: "{{ ds8000_password }}"
    name: volume_name_test
    state: absent
'''

RETURN = r''' # '''

from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule

from ..module_utils.ds8000 import PyDs8k, ds8000_argument_spec


class PyDs8kHelper(PyDs8k):
    def __init__(self, module):
        super(PyDs8kHelper, self).__init__(module)
        self.changed = False
        self.failed = False

    def _ds8000_volume_present(self):
        result = {}
        changed, failed = self._create_ds8000_volume()
        result = {'changed': changed, 'failed': failed}
        return result

    def _create_ds8000_volume(self):
        changed = False
        failed = False
        client = self.client
        volume_type = self.params['volume_type']
        try:
            if volume_type == 'fb':
                client.create_volume_fb(
                    name=self.params['name'],
                    cap=self.params['capacity'],
                    pool=self.params['pool'],
                    tp=self.params['storage_allocation_method'],
                    captype=self.params['capacity_type'],
                    lss=self.params['lss'])
                changed = True
            elif volume_type == 'ckd':
                client.create_volume_ckd(
                    name=self.params['name'],
                    cap=self.params['capacity'],
                    pool=self.params['pool'],
                    tp=self.params['storage_allocation_method'],
                    captype=self.params['capacity_type'],
                    lss=self.params['lss'])
        except Exception as generic_exc:
            failed = True
            self.module.fail_json(
                msg="Failed to create volumes on DS8000 storage. "
                "ERR: {error}".format(
                    error=to_native(generic_exc)))
        return changed, failed

    def _ds8000_volume_absent(self, volume_name='', volume_id=''):
        result = {}
        if volume_name:
            volume_ids = self._get_volume_ids_from_name(volume_name)
            if volume_ids:
                for volume_id_temp in volume_ids:
                    changed, failed = self._delete_ds8000_volume(
                        volume_id_temp, volume_name)
                    result = {'changed': changed, 'failed': failed}
        elif volume_id:
            volume_name_of_id = self._get_volume_name(volume_id)
            if volume_name_of_id:
                changed, failed = self._delete_ds8000_volume(
                    volume_id, volume_name_of_id)
                result = {'changed': changed, 'failed': failed}
        return result

    def _get_volume_name(self, volume_id):
        volumes = self._get_all_volumes_on_ds8000_storage()
        for volume in volumes:
            if volume['id'] == volume_id:
                return volume['name']
        return ''

    def _delete_ds8000_volume(self, volume_id, volume_name):
        changed = False
        failed = False
        client = self.client
        try:
            client.delete_volume(volume_id)
            changed = True
        except Exception as generic_exc:
            failed = True
            self.module.fail_json(
                msg="Failed to delete the volume {volume_name} from DS8000 storage. "
                    "ERR: {error}".format(
                        volume_name=volume_name, error=to_native(generic_exc)))
        return changed, failed


def main():
    argument_spec = ds8000_argument_spec()
    argument_spec.update(
        name=dict(
            type='str'), state=dict(
                type='str', default='present', choices=[
                    'absent', 'present']), volume_type=dict(
                        type='str', default='fb', choices=[
                            'fb', 'ckd']), pool=dict(
                                type='str'), capacity=dict(
                                    type='str'), capacity_type=dict(
                                        type='str', default='gib', choices=[
                                            'gib', 'bytes', 'cyl', 'mod1']), lss=dict(
                                                type='str'), storage_allocation_method=dict(
                                                    type='str', default='none', choices=[
                                                        'none', 'ese', 'tse']), volume_id=dict(
                                                            type='str'))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=[
            ['name', 'volume_id'],
        ],
    )

    pds8kh = PyDs8kHelper(module)

    if module.params['state'] == 'present':
        result = pds8kh._ds8000_volume_present()
    elif module.params['state'] == 'absent':
        if 'volume_id' in module.params and module.params['volume_id']:
            result = pds8kh._ds8000_volume_absent(module.params['volume_id'])
        elif 'name' in module.params and module.params['name']:
            result = pds8kh._ds8000_volume_absent(module.params['name'])

    if 'failed' not in result:
        result['failed'] = False

    if result['failed']:
        module.fail_json(**result)
    else:
        module.exit_json(**result)


if __name__ == '__main__':
    main()
