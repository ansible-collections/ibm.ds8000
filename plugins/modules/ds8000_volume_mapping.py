#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (C) 2021 IBM CORPORATION
# Apache License, Version 2.0 (see https://opensource.org/licenses/Apache-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: ds8000_volume_mapping
short_description: Manage DS8000 volume mapping to hosts
description:
  - Manage DS8000 volume mapping to hosts.
version_added: "1.0.0"
author: Matan Carmeli (@matancarmeli7)
options:
  name:
    description:
      - The name of the DS8000 host to work with.
    type: str
    required: true
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
      - To use a specific volume, use I(volume_id)
    type: str
notes:
  - Supports C(check_mode).
extends_documentation_fragment:
  - ibm.ds8000.ds8000.documentation
'''

EXAMPLES = r'''
- name: Ensure that a volume is mapped to a host in the storage
  ibm.ds8000.ds8000_volume_mapping:
    hostname: "{{ ds8000_host }}"
    username: "{{ ds8000_username }}"
    password: "{{ ds8000_password }}"
    name: host_name_test
    state: present
    volume_id: "0000"

- name: Ensure that a volume is not mapped to a host in the storage
  ibm.ds8000.ds8000_volume_mapping:
    hostname: "{{ ds8000_host }}"
    username: "{{ ds8000_username }}"
    password: "{{ ds8000_password }}"
    name: host_name_test
    state: absent
    volume_id: "0000"
'''

RETURN = r''' # '''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.text.converters import to_native
from ansible_collections.ibm.ds8000.plugins.module_utils.ds8000 import Ds8000ManagerBase, ds8000_argument_spec


class VolumeMapper(Ds8000ManagerBase):
    def ensure_volume_mapped_to_host(self, volume_id):
        result = self._verify_volume_mapping_state(volume_id, self._map_volume_to_host)
        return result

    def ensure_volume_unmapped_from_host(self, volume_id):
        result = self._verify_volume_mapping_state(volume_id, self._unmap_volume_from_host)
        return result

    def _verify_volume_mapping_state(self, volume_id, volume_mapping_state):
        volume_mapping_on_host = self._get_volumes_mapping_on_specific_host()
        volume_map = None
        for volume_map in volume_mapping_on_host:
            if volume_id == volume_map.volume:
                volume_mapping_state(volume_id, volume_map)
                return {'changed': self.changed, 'failed': self.failed}
        volume_mapping_state(volume_id, volume_map)

        return {'changed': self.changed, 'failed': self.failed}

    def _map_volume_to_host(self, volume_id, volume_map_on_the_host):
        if volume_map_on_the_host:
            if volume_id == volume_map_on_the_host.volume:
                return
        name = self.params['name']
        try:
            if not self.module.check_mode:
                self.client.map_volume_to_host(host_name=name, volume_id=volume_id)
            self.changed = True
        except Exception as generic_exc:
            self.failed = True
            self.module.fail_json(
                msg="Failed to map volume id {volume_id} to host {host_name} on the DS8000 storage system. "
                "ERR: {error}".format(volume_id=volume_id, host_name=name, error=to_native(generic_exc))
            )

    def _get_volumes_mapping_on_specific_host(self):
        name = self.params['name']
        volume_mappings = []
        volume_mappings_by_host = self.client.get_mappings_by_host(host_name=name)
        for volume_map in volume_mappings_by_host:
            volume_mappings.append(volume_map)
        return volume_mappings

    def _unmap_volume_from_host(self, volume_id_on_the_host, volume_map):
        if not volume_map:
            return
        if volume_id_on_the_host != volume_map.volume:
            return
        name = self.params['name']
        lun_id = volume_map.lunid
        try:
            if not self.module.check_mode:
                self.client.unmap_volume_from_host(host_name=name, lunid=lun_id)
            self.changed = True
        except Exception as generic_exc:
            self.failed = True
            self.module.fail_json(
                msg="Failed to unmap volume id {volume_id} from host {host_name} on the DS8000 storage system."
                " ERR: {error}".format(volume_id=volume_map.volume, host_name=name, error=to_native(generic_exc))
            )


def ensure_volume_mapping_state(volume_id, module, volume_mapper):
    if module.params['state'] == 'present':
        result = volume_mapper.ensure_volume_mapped_to_host(volume_id)
    elif module.params['state'] == 'absent':
        result = volume_mapper.ensure_volume_unmapped_from_host(volume_id)
    return result


def main():
    argument_spec = ds8000_argument_spec()
    argument_spec.update(
        name=dict(type='str', required=True),
        state=dict(type='str', default='present', choices=['absent', 'present']),
        volume_id=dict(type='str'),
        volume_name=dict(type='str'),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=[
            ['volume_name', 'volume_id'],
        ],
        supports_check_mode=True,
    )

    volume_mapper = VolumeMapper(module)

    if volume_mapper.verify_ds8000_object_exist(volume_mapper.client.get_host, host_name=module.params['name']):
        if module.params.get('volume_name'):
            volume_ids = volume_mapper.get_volume_ids_from_name(module.params['volume_name'])
            for volume_id in volume_ids:
                result = ensure_volume_mapping_state(volume_id, module, volume_mapper)
        else:
            result = ensure_volume_mapping_state(module.params['volume_id'], module, volume_mapper)
    else:
        volume_mapper.failed = True
        result = {'changed': volume_mapper.changed, 'failed': volume_mapper.failed}

    if result['failed']:
        module.fail_json(**result)
    else:
        module.exit_json(**result)


if __name__ == '__main__':
    main()
