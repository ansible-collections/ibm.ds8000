#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2021, Matan Carmeli <matan.carmeli7@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
author: Matan Carmeli (@matancarmeli7)
module: ibm.ds8000.ds8000_volume_info
short_description: Return basic info on DS8000 volumes
description:
  - Return basic information pertaining to a DS8000 volumes.
  - If the host and pool parameters are not set, it will give information on all the volumes in the storage.
options:
  host:
    description:
      - The host that the volumes are mapped to.
    type: str
  pool:
    description:
      - The pool that the volumes are belong to.
    type: str
extends_documentation_fragment:
  - ibm.ds8000.ds8000.documentation
'''

EXAMPLES = r'''
- name: get all the volumes under host
  ibm.ds8000.ds8000_volume_info:
    hostname: "{{ ds8000_host }}"
    username: "{{ ds8000_username }}"
    password: "{{ ds8000_password }}"
    host: host_name_test

- name: get all the volumes under host
  ibm.ds8000.ds8000_volume_info:
    hostname: "{{ ds8000_host }}"
    username: "{{ ds8000_username }}"
    password: "{{ ds8000_password }}"
    pool: pool_name_test

- name: get all the volumes
  ibm.ds8000.ds8000_volume_info:
    hostname: "{{ ds8000_host }}"
    username: "{{ ds8000_username }}"
    password: "{{ ds8000_password }}"
'''

RETURN = r'''
virtual_machines:
  description: list of dictionary of volumes and their information
  returned: success
  type: list
  sample: [
    {
        "name": "volume_name",
        "id": "volume_id"
    }
  ]
'''

from ansible.module_utils.basic import AnsibleModule

from ..module_utils.ds8000 import PyDs8k, ds8000_argument_spec

DEFAULT_POOLS_URL = '/pools'
DEFAULT_HOSTS_URL = '/hosts'


class PyDs8kHelper(PyDs8k):
    def __init__(self, module):
        super(PyDs8kHelper, self).__init__(module)
        self.changed = False
        self.failed = False

    def _ds8000_volume_info(self):
        volumes_by_host = []
        volumes_by_pool = []
        if self.params['host']:
            hosts = self._get_list_of_ds8000_object(
                DEFAULT_HOSTS_URL, 'hosts')
            if self.params['host'] in hosts[1]:
                volumes_by_host = self._get_list_of_ds8000_object(
                    '/hosts/{hosts}/volumes'.format(hosts=self.params['host']), 'volumes')
                volumes_by_host = volumes_by_host[0]
            else:
                self.module.fail_json(
                    msg="The host {hosts} is not exists".format(
                        hosts=self.params['host']))
        if self.params['pool']:
            pools = self._get_list_of_ds8000_object(
                DEFAULT_POOLS_URL, 'pools')
            if self.params['pool'] in pools[1]:
                volumes_by_pool = self._get_list_of_ds8000_object(
                    '/pools/{pool}/volumes'.format(pool=self.params['pool']), 'volumes')
                volumes_by_pool = volumes_by_pool[0]
            else:
                self.module.fail_json(
                    msg="The pool {pool} is not exists".format(
                        pool=self.params['pool']))
        if len(volumes_by_host) > 0 and len(volumes_by_pool) > 0:
            wanted_volumes = [
                temp_volume_dict for temp_volume_dict in volumes_by_host if temp_volume_dict in volumes_by_pool]
            return wanted_volumes
        elif len(volumes_by_host) > 0 and len(volumes_by_pool) == 0:
            return volumes_by_host
        elif len(volumes_by_host) == 0 and len(volumes_by_pool) > 0:
            return volumes_by_pool
        else:
            volumes = self._get_all_volumes_on_ds8000_storage()
            return volumes


def main():
    argument_spec = ds8000_argument_spec()
    argument_spec.update(
        host=dict(type='str'),
        pool=dict(type='str')
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
    )

    pds8kh = PyDs8kHelper(module)

    _volumes = pds8kh._ds8000_volume_info()

    module.exit_json(changed=False, volumes=_volumes)


if __name__ == '__main__':
    main()
