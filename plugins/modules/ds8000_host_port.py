#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (C) 2021 IBM CORPORATION
# Apache License, Version 2.0 (see https://opensource.org/licenses/Apache-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: ds8000_host_port
short_description: Manage host ports for a DS8000 host
description:
  - Manage host ports for a DS8000 host.
version_added: "1.0.0"
author: Matan Carmeli (@matancarmeli7)
options:
  name:
    description:
      - The name of the DS8000 host to work with.
      - Required when I(state=present).
    type: str
  state:
    description:
      - Specify the state the DS8000 host port should be in.
    type: str
    default: present
    choices:
      - present
      - absent
  host_port:
    description:
      - List of host port WWPNs to assign to a specific host on the DS8000 storage system.
    required: true
    type: list
    elements: str
  force:
    description:
      - Optional when I(state=present).
      - If C(yes), if a host port is assigned to another host, it will transfer it to the host specified.
      - If C(no), if a host port is assigned to another host, it will not transfer it to the host specified.
    default: no
    type: bool
notes:
  - Supports C(check_mode).
extends_documentation_fragment:
  - ibm.ds8000.ds8000.documentation
'''

EXAMPLES = r'''
- name: Create and assign some host ports to the host
  ibm.ds8000.ds8000_host_port:
    hostname: "{{ ds8000_host }}"
    username: "{{ ds8000_username }}"
    password: "{{ ds8000_password }}"
    name: host_name_test
    state: present
    force: no
    host_port:
      - 10000000C9A1BAB2
      - 10000000C9A1BAB3

- name: Assign some host ports to the host even though they are already assigned to another host
  ibm.ds8000.ds8000_host_port:
    hostname: "{{ ds8000_host }}"
    username: "{{ ds8000_username }}"
    password: "{{ ds8000_password }}"
    name: host_name_test
    state: present
    force: yes
    host_port: 10000000C9A1BAB2

- name: Delete some host ports from the DS8000 storage
  ibm.ds8000.ds8000_host_port:
    hostname: "{{ ds8000_host }}"
    username: "{{ ds8000_username }}"
    password: "{{ ds8000_password }}"
    state: absent
    host_port: 10000000C9A1BAB2
'''

RETURN = r''' # '''

try:
    import pyds8k.exceptions
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.text.converters import to_native
from ansible_collections.ibm.ds8000.plugins.module_utils.ds8000 import Ds8000ManagerBase, ds8000_argument_spec, ABSENT, PRESENT


class HostPortManager(Ds8000ManagerBase):
    def host_port_present(self):
        if self.verify_ds8000_object_exist(self.client.get_host, host_name=self.params['name']):
            for host_port in self.params['host_port']:
                host_port = host_port.replace(':', '')
                self.verify_assign_host_port(host_port)
        return {'changed': self.changed, 'failed': self.failed}

    def host_port_absent(self):
        for host_port in self.params['host_port']:
            host_port = host_port.replace(':', '')
            self.verify_delete_host_port(host_port)
        return {'changed': self.changed, 'failed': self.failed}

    def verify_assign_host_port(self, host_port):
        existing_host_port_object = self._does_host_port_exist(port_id=host_port)
        if existing_host_port_object:
            if not self._does_host_port_bound_to_host(existing_host_port_object):
                if not self._does_host_port_bound_to_other_hosts(existing_host_port_object) and self._is_host_port_unconfigured(existing_host_port_object):
                    self._assign_host_port_to_host(host_port)
                else:
                    if not self.params['force']:
                        self.failed = True
                        self.module.fail_json(
                            msg="The WWPN {host_port} is assigned to another host ({host}) on the DS8000 storage. "
                            "To assign it to its desired host, use the force: true parameter.".format(host_port=host_port, host=existing_host_port_object.host)
                        )
                    else:
                        self._assign_host_port_to_host(host_port)
        else:
            self._create_host_port(host_port)
        return {'changed': self.changed, 'failed': self.failed}

    def _assign_host_port_to_host(self, host_port):
        name = self.params['name']
        try:
            if not self.module.check_mode:
                self.client.update_host_port_change_host(port_id=host_port, host_name=name)
            self.changed = True
        except pyds8k.exceptions.BadRequest as bad_wwpn:
            self.failed = True
            self.module.fail_json(msg="This WWPN {host_port} not found. " "ERR: {error}".format(host_port=host_port, error=to_native(bad_wwpn)))
        except Exception as generic_exc:
            self.failed = True
            self.module.fail_json(
                msg="Failed to assign this {host_port} WWPN to the host {host_name}. "
                "ERR: {error}".format(host_port=host_port, host_name=name, error=to_native(generic_exc))
            )

    def _create_host_port(self, host_port):
        name = self.params['name']
        try:
            if not self.module.check_mode:
                self.client.create_host_port(port_id=host_port, host_name=name)
            self.changed = True
        except Exception as generic_exc:
            self.failed = True
            self.module.fail_json(
                msg="Failed to create the host port {host_port} on the DS8000 storage system. "
                "ERR: {error}".format(host_port=host_port, error=to_native(generic_exc))
            )

    def _does_host_port_bound_to_other_hosts(self, host_port_object):
        name = self.params['name']
        if host_port_object.host:
            if name not in host_port_object.host:
                return True
        return False

    def _does_host_port_bound_to_host(self, host_port_object):
        name = self.params['name']
        if host_port_object.host:
            if name in host_port_object.host:
                return True
        return False

    def _is_host_port_unconfigured(self, host_port_object):
        if 'unconfigured' in host_port_object.state:
            return True
        return False

    def verify_delete_host_port(self, host_port):
        if self._does_host_port_exist(host_port):
            if not self.module.check_mode:
                self._delete_host_port(host_port)
        return {'changed': self.changed, 'failed': self.failed}

    def _delete_host_port(self, host_port):
        try:
            if not self.module.check_mode:
                self.client.delete_host_port(port_id=host_port)
            self.changed = True
        except Exception as generic_exc:
            self.failed = True
            self.module.fail_json(
                msg="Failed to delete the host port {host_port} from the DS8000 storage system. "
                "ERR: {error}".format(host_port=host_port, error=to_native(generic_exc))
            )

    def _does_host_port_exist(self, port_id):
        return self.does_ds8000_object_exist(self.client.get_host_port, port_id=port_id)


def main():
    argument_spec = ds8000_argument_spec()
    argument_spec.update(
        name=dict(type='str'),
        state=dict(type='str', default=PRESENT, choices=[ABSENT, PRESENT]),
        host_port=dict(type='list', elements='str', required=True),
        force=dict(type='bool', default=False),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    host_port_manager = HostPortManager(module)

    if module.params['state'] == PRESENT:
        result = host_port_manager.host_port_present()
    elif module.params['state'] == ABSENT:
        result = host_port_manager.host_port_absent()

    if result['failed']:
        module.fail_json(**result)
    else:
        module.exit_json(**result)


if __name__ == '__main__':
    main()
