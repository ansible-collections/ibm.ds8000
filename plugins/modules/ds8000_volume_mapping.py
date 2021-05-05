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
module: ds8000_volume_mapping
short_description: Manage DS8000 volume mapping to hosts.
description:
  - Manage DS8000 volume mapping to hosts.
options:
  name:
    description:
      - The name of the DS8000 host to work with.
    type: str
  state:
    description:
    - Specify the state the DS8000 volume mapping should be in.
    type: str
    default: present
    choices:
      - present
      - absent
  volume_id:
    description:
      - The volume ID of the volume that you want to map to a host.
    type: str
  volume_name:
    description:
      - The volume name that you want to map to a host.
      - Notice that different volumes sometimes have the same volume name, so it will map all of them.
      - To use a specific volume, use C(volume_id)
    type: str
extends_documentation_fragment:
  - ibm.ds8000.ds8000.documentation
'''

EXAMPLES = r'''
- name: Ensure that a host exists in the storage
  ibm.ds8000.ds8000_volume_mapping:
    hostname: "{{ ds8000_host }}"
    username: "{{ ds8000_username }}"
    password: "{{ ds8000_password }}"
    name: host_name_test
    state: present

- name: Ensure that a host does not exist in the storage
  ibm.ds8000.ds8000_volume_mapping:
    hostname: "{{ ds8000_host }}"
    username: "{{ ds8000_username }}"
    password: "{{ ds8000_password }}"
    name: host_name_test
    state: absent
'''

RETURN = r''' # '''

import json
from ansible_collections.ibm.ds8000.plugins.module_utils.ds8000 import (Ds8000ManagerBase, ds8000_argument_spec)
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


class VolumeMapper(Ds8000ManagerBase):
    def verify_volume_mapping_state(self, volume_id, volume_mapping_state):
        volume_mapping_on_host = self._get_volume_mapping_on_specific_host()
        volume_map = None
        for volume_map in volume_mapping_on_host:
            if volume_id == volume_map['volume']['id']:
                volume_mapping_state(volume_id, volume_map)
                return {'changed': self.changed, 'failed': self.failed}
        volume_mapping_state(volume_id, volume_map)
        return {'changed': self.changed, 'failed': self.failed}

    def map_volume_to_host(self, volume_id, volume_map_on_the_host):
        if volume_map_on_the_host:
            if volume_id == volume_map_on_the_host['volume']['id']:
                return
        name = self.params['name']
        try:
            self.client.map_volume_to_host(host_name=name,
                                           volume_id=volume_id)
            self.changed = True
        except Exception as generic_exc:
            self.failed = True
            self.module.fail_json(
                msg="Failed to map volume id {volume_id} to {host_name} host on DS8000 storage. "
                "ERR: {error}".format(
                    volume_id=volume_id,
                    host_name=name,
                    error=to_native(generic_exc)))

    def _get_volume_mapping_on_specific_host(self):
        name = self.params['name']
        volume_mappings = []
        sub_url = '/hosts/{host_name}/mappings'.format(host_name=name)
        response = self.get_ds8000_object_from_server(sub_url)
        parsed_response = json.loads(response.text)['data']['mappings']
        for volume_map in parsed_response:
            volume_mappings.append(volume_map)
        return volume_mappings

    def unmap_volume_from_host(self, volume_id_on_the_host, volume_map):
        if not volume_map:
            return
        if volume_id_on_the_host != volume_map['volume']['id']:
            return
        name = self.params['name']
        lun_id = volume_map['lunid']
        try:
            self.client.unmap_volume_from_host(host_name=name,
                                               lunid=lun_id)
            self.changed = True
        except Exception as generic_exc:
            self.failed = True
            self.module.fail_json(
                msg="Failed to unmap volume id {volume_id} from {host_name} host on DS8000 storage."
                " ERR: {error}".format(
                    volume_id=volume_map['volume']['id'],
                    host_name=name,
                    error=to_native(generic_exc)))


def ensure_volume_mapping_state(volume_id, module, volume_mapper):
    if module.params['state'] == 'present':
        result = volume_mapper.verify_volume_mapping_state(volume_id,
                                                           volume_mapper.map_volume_to_host)
    elif module.params['state'] == 'absent':
        result = volume_mapper.verify_volume_mapping_state(volume_id,
                                                           volume_mapper.unmap_volume_from_host)
    return result


def main():
    argument_spec = ds8000_argument_spec()
    argument_spec.update(
        name=dict(type='str'),
        state=dict(type='str',
                   default='present', choices=['absent', 'present']),
        volume_id=dict(type='str'),
        volume_name=dict(type='str'))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=[
            ['volume_name', 'volume_id'],
        ],
    )

    volume_mapper = VolumeMapper(module)

    if volume_mapper.verify_ds8000_object_exist('name', 'hosts'):
        if module.params.get('volume_name'):
            volume_ids = volume_mapper.get_volume_ids_from_name(
                module.params['volume_name'])
            for volume_id in volume_ids:
                result = ensure_volume_mapping_state(volume_id, module, volume_mapper)
        else:
            result = ensure_volume_mapping_state(
                module.params['volume_id'], module, volume_mapper)
    else:
        volume_mapper.failed = True
        result = {'changed': volume_mapper.changed, 'failed': volume_mapper.failed}

    if result['failed']:
        module.fail_json(**result)
    else:
        module.exit_json(**result)


if __name__ == '__main__':
    main()
