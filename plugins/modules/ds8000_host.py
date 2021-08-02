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
      - The name of the DS8000 host to work with.
    type: str
  state:
    description:
    - Specify the state the DS8000 host should be in.
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
- name: Ensure that a host exists in the storage
  ibm.ds8000.ds8000_host:
    hostname: "{{ ds8000_host }}"
    username: "{{ ds8000_username }}"
    password: "{{ ds8000_password }}"
    name: host_name_test
    state: present

- name: Ensure that a host does not exist in the storage
  ibm.ds8000.ds8000_host:
    hostname: "{{ ds8000_host }}"
    username: "{{ ds8000_username }}"
    password: "{{ ds8000_password }}"
    name: host_name_test
    state: absent
'''

RETURN = r''' # '''

from ansible.module_utils.common.text.converters import to_native
from ansible.module_utils.basic import AnsibleModule

from ansible_collections.ibm.ds8000.plugins.module_utils.ds8000 import (Ds8000ManagerBase, ds8000_argument_spec,
                                                                        ABSENT, PRESENT)


class HostManager(Ds8000ManagerBase):
    def ensure_host_present(self):
        result = self._verify_host_state(self._add_host)
        return result

    def ensure_host_absent(self):
        result = self._verify_host_state(self._remove_host)
        return result

    def _verify_host_state(self, host_state):
        host_state()
        return {'changed': self.changed, 'failed': self.failed}

    def _add_host(self):
        name = self.params['name']
        host_type = self.params['host_type']
        if not self.does_ds8000_object_exist('name', self.client.get_hosts()):
            try:
                self.client.create_host(host_name=name, hosttype=host_type)
                self.changed = True
            except Exception as generic_exc:
                self.failed = True
                self.module.fail_json(
                    msg="Failed to add {host_name} host to the DS8000 storage. ERR: {error}".format(
                        host_name=name, error=to_native(generic_exc)))

    def _remove_host(self):
        name = self.params['name']
        if self.does_ds8000_object_exist('name', self.client.get_hosts()):
            try:
                self.client.delete_host(host_name=name)
                self.changed = True
            except Exception as generic_exc:
                self.failed = True
                self.module.fail_json(
                    msg="Failed to remove {host_name} host from the DS8000 storage."
                        " ERR: {error}".format(
                            host_name=name, error=to_native(generic_exc)))


def main():
    argument_spec = ds8000_argument_spec()
    argument_spec.update(
        name=dict(type='str'),
        state=dict(
            type='str',
            default=PRESENT,
            choices=[
                ABSENT,
                PRESENT]),
        host_type=dict(type='str', default='Linuxrhel')
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
    )

    host_manager = HostManager(module)

    if module.params['state'] == PRESENT:
        result = host_manager.ensure_host_present()
    elif module.params['state'] == ABSENT:
        result = host_manager.ensure_host_absent()

    if result['failed']:
        module.fail_json(**result)
    else:
        module.exit_json(**result)


if __name__ == '__main__':
    main()
