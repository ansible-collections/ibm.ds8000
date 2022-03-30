#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (C) 2021 IBM CORPORATION
# Apache License, Version 2.0 (see https://opensource.org/licenses/Apache-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: ds8000_host
short_description: Manage DS8000 hosts
description:
  - Manage DS8000 hosts.
version_added: "1.0.0"
author: Matan Carmeli (@matancarmeli7)
options:
  name:
    description:
      - The name of the DS8000 host to work with.
    required: true
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
    - The host type of the host that will be created on the DS8000 storage system.
    type: str
    default: Linux
notes:
  - Supports C(check_mode).
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

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.text.converters import to_native
from ansible_collections.ibm.ds8000.plugins.module_utils.ds8000 import Ds8000ManagerBase, ds8000_argument_spec, ABSENT, PRESENT


class HostManager(Ds8000ManagerBase):
    def host_present(self):
        self._create_host()
        return {'changed': self.changed, 'failed': self.failed}

    def host_absent(self):
        self._delete_host()
        return {'changed': self.changed, 'failed': self.failed}

    def _create_host(self):
        name = self.params['name']
        host_type = self.params['host_type']
        if not self._does_host_exist():
            try:
                if not self.module.check_mode:
                    self.client.create_host(host_name=name, hosttype=host_type)
                self.changed = True
            except Exception as generic_exc:
                self.failed = True
                self.module.fail_json(
                    msg="Failed to create the host {host_name} on the DS8000 storage. ERR: {error}".format(host_name=name, error=to_native(generic_exc))
                )

    def _delete_host(self):
        name = self.params['name']
        if self._does_host_exist():
            try:
                if not self.module.check_mode:
                    self.client.delete_host(host_name=name)
                self.changed = True
            except Exception as generic_exc:
                self.failed = True
                self.module.fail_json(
                    msg="Failed to delete the host {host_name} from the DS8000 storage. ERR: {error}".format(host_name=name, error=to_native(generic_exc))
                )

    def _does_host_exist(self):
        return self.does_ds8000_object_exist(self.client.get_host, host_name=self.params['name'])


def main():
    argument_spec = ds8000_argument_spec()
    argument_spec.update(
        name=dict(type='str', required=True), state=dict(type='str', default=PRESENT, choices=[ABSENT, PRESENT]), host_type=dict(type='str', default='Linux')
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    host_manager = HostManager(module)

    if module.params['state'] == PRESENT:
        result = host_manager.host_present()
    elif module.params['state'] == ABSENT:
        result = host_manager.host_absent()

    if result['failed']:
        module.fail_json(**result)
    else:
        module.exit_json(**result)


if __name__ == '__main__':
    main()
