#!/usr/bin/python

from __future__ import division, print_function

__metaclass__ = type

import json
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native

from ..module_utils.ds8000 import (
    PyDs8k, ds8000_argument_spec, costume_get_request)


class PyDs8kHelper(PyDs8k):
    def __init__(self, module):
        super(PyDs8kHelper, self).__init__(module)
        self.changed = False
        self.failed = False

    def _ds8000_volume_mapping_present(self, volume_id):
        result = {}
        changed = False
        failed = False
        volume_mappinng_on_host = self._get_volume_mapping_on_specific_host()
        for volume_map in volume_mappinng_on_host:
            if volume_id == volume_map['volume']['id']:
                result = {'changed': changed, 'failed': failed}
                return result
        changed, failed = self._map_volume_to_host(volume_id)
        result = {'changed': changed, 'failed': failed}
        return result

    def _map_volume_to_host(self, volume_id):
        name = self.params['name']
        client = self.client
        changed = False
        failed = False
        try:
            client.map_volume_to_host(host_name=name,
                                      volume_id=volume_id)
            changed = True
        except Exception as generic_exc:
            failed = True
            self.module.fail_json(
                msg="Failed to map volume id {} to {} host on DS8000 storage. "
                "ERR: {}".format(
                    volume_id, name, to_native(generic_exc)))
        return changed, failed

    def _ds8000_volume_mapping_absent(self, volume_id):
        result = {}
        changed = False
        failed = False
        volume_mappinng_on_host = self._get_volume_mapping_on_specific_host()
        for volume_map in volume_mappinng_on_host:
            if volume_id == volume_map['volume']['id']:
                changed, failed = self._unmap_volume_from_host(volume_map)
        result = {'changed': changed, 'failed': failed}
        return result

    def _get_volume_mapping_on_specific_host(self):
        token = self.token
        name = self.params['name']
        volume_mappings = []
        sub_url = '/hosts/{}/mappings'.format(name)
        headers = {
            "Content-Type": "application/json",
            "X-Auth-Token": "{}".format(token)
        }
        response = costume_get_request(self.module, headers, sub_url)
        res = json.loads(response.text)
        for volume_map in res['data']['mappings']:
            volume_mappings.append(volume_map)
        return volume_mappings

    def _unmap_volume_from_host(self, volume_map):
        changed = False
        failed = False
        name = self.params['name']
        lun_id = volume_map['lunid']
        client = self.client
        try:
            client.unmap_volume_from_host(host_name=name,
                                          lunid=lun_id)
            changed = True
        except Exception as generic_exc:
            failed = True
            self.module.fail_json(
                msg="Failed to unmap volume id {} from {} host on DS8000 storage. "
                "ERR: {}".format(
                    volume_map['volume']['id'],
                    name,
                    to_native(generic_exc)))
        return changed, failed


def map_or_unmap_volume(volume_id, module, pds8kh):
    if module.params['state'] == 'present':
        result = pds8kh._ds8000_volume_mapping_present(volume_id)
    elif module.params['state'] == 'absent':
        result = pds8kh._ds8000_volume_mapping_absent(volume_id)
    return result


def main():
    argument_spec = ds8000_argument_spec()
    argument_spec.update(
        name=dict(
            type='str'), state=dict(
            type='str', default='present', choices=[
                'absent', 'present']), volume_id=dict(
                    type='str'), volume_name=dict(
                        type='str'))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=[
            ['volume_name', 'volume_id'],
        ],
    )

    pds8kh = PyDs8kHelper(module)

    if not pds8kh._check_if_ds8000_host_exists():
        result = {'changed': False, 'failed': True}
    else:
        if 'volume_name' in module.params and module.params['volume_name']:
            volume_ids = pds8kh._get_volume_ids_from_name(
                module.params['volume_name'])
            for volume_id in volume_ids:
                result = map_or_unmap_volume(volume_id, module, pds8kh)
        else:
            result = map_or_unmap_volume(
                module.params['volume_id'], module, pds8kh)

    if 'failed' not in result:
        result['failed'] = False

    if result['failed']:
        module.fail_json(**result)
    else:
        module.exit_json(**result)


if __name__ == '__main__':
    main()
