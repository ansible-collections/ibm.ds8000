#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2021, Matan Carmeli <matan.carmeli7@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
author: Matan Carmeli (@matancarmeli7)
module: ds8000_host
short_description: Manage DS8000 hosts
description:
  - Manage DS8000 hosts.
options:
  name:
    description:
      - The Name of the DS8000 host to work with.
    type: str
  state:
    description:
    - If the module will ensure the host will be presented on the DS8000 storage or not.
    type: str
    default: present
    choices:
      - present
      - absent
  host_type:
    description:
    - The host type of the host that will be created at DS8000 storage.
    type: str
    default: Linuxrhel
extends_documentation_fragment:
  - ibm.ds8000.ds8000.documentation
'''

EXAMPLES = r'''
- name: Ensure that a host is exists on the storage
  ibm.ds8000.ds8000_host:
    hostname: "{{ ds8000_host }}"
    username: "{{ ds8000_username }}"
    password: "{{ ds8000_password }}"
    name: host_name_test
    state: present

- name: Ensure that a host does not exists on the storage
  ibm.ds8000.ds8000_host:
    hostname: "{{ ds8000_host }}"
    username: "{{ ds8000_username }}"
    password: "{{ ds8000_password }}"
    name: host_name_test
    state: absent
'''

RETURN = r''' # '''

from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule

from ..module_utils.ds8000 import PyDs8k, ds8000_argument_spec


class PyDs8kHelper(PyDs8k):
    def __init__(self, module):
        super(PyDs8kHelper, self).__init__(module)

    def _ds8000_host_present(self):
        result = {}
        changed, failed = self._add_host_to_ds8000()
        result = {'changed': changed, 'failed': failed}
        return result

    def _add_host_to_ds8000(self):
        changed = False
        failed = False
        name = self.params['name']
        hosttype = self.params['host_type']
        client = self.client
        if not self._check_if_the_host_exists():
            try:
                client.create_host(host_name=name, hosttype=hosttype)
                changed = True
            except Exception as generic_exc:
                failed = True
                self.module.fail_json(
                    msg="Failed to add {host_name} host to the DS8000 storage. Err: {error}".format(
                        host_name=name, error=to_native(generic_exc)))
        return changed, failed

    def _check_if_the_host_exists(self):
        name = self.params['name']
        module = self.module
        hosts = self._get_all_hosts()
        if name not in hosts:
            return False
        return True

    def _ds8000_host_absent(self):
        result = {}
        changed, failed = self._remove_host_from_ds8000()
        result = {'changed': changed, 'failed': failed}
        return result

    def _remove_host_from_ds8000(self):
        changed = False
        failed = False
        name = self.params['name']
        hosttype = self.params['host_type']
        client = self.client
        if self._check_if_the_host_exists():
            try:
                client.delete_host(host_name=name)
                changed = True
            except Exception as generic_exc:
                failed = True
                self.module.fail_json(
                    msg="Failed to remove {host_name} host from the DS8000 storage. ERR: {error}".format(
                        host_name=name, error=to_native(generic_exc)))
        return changed, failed


def main():
    argument_spec = ds8000_argument_spec()
    argument_spec.update(
        name=dict(type='str'),
        state=dict(
            type='str',
            default='present',
            choices=[
                'absent',
                'present']),
        host_type=dict(type='str', default='Linuxrhel')
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
    )

    pds8kh = PyDs8kHelper(module)

    if module.params['state'] == 'present':
        result = pds8kh._ds8000_host_present()
    elif module.params['state'] == 'absent':
        result = pds8kh._ds8000_host_absent()

    if 'failed' not in result:
        result['failed'] = False

    if result['failed']:
        module.fail_json(**result)
    else:
        module.exit_json(**result)


if __name__ == '__main__':
    main()
