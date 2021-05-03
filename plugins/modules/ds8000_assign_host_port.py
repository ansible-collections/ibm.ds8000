#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2021, Matan Carmeli <matan.carmeli7@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
author: Matan Carmeli (@matancarmeli7)
module: ds8000_assign_host_port
short_description: Assign host ports to a DS8000 host.
description:
  - Assign host ports to a DS8000 host.
options:
  name:
    description:
      - The name of the DS8000 host to work with.
    type: str
  host_port:
    description:
    - list of host_ports to assign to a specific host in DS8000 storage.
    type: list
    elements: str
  force:
    description:
      - If set to True, in case that a host port is assigned to another host, it will transfer it to the host that specified.
      - If set to False, in case that a host port is assigned to another host, it will not transfer it to the host that specified.
    default: False
    type: bool
extends_documentation_fragment:
  - ibm.ds8000.ds8000.documentation
'''

EXAMPLES = r'''
- name: Assign some host ports to host with force on false
  ibm.ds8000.ds8000_assign_host_port:
    hostname: "{{ ds8000_host }}"
    username: "{{ ds8000_username }}"
    password: "{{ ds8000_password }}"
    name: host_name_test
    force: False
    host_port:
      - 10000000C9A1BAB2
      - 10000000C9A1BAB3

- name: Assign some host ports to host with force on true
  ibm.ds8000.ds8000_assign_host_port:
    hostname: "{{ ds8000_host }}"
    username: "{{ ds8000_username }}"
    password: "{{ ds8000_password }}"
    name: host_name_test
    force: True
    host_port: 10000000C9A1BAB2
'''

RETURN = r''' # '''

import json

try:
    import pyds8k.exceptions
except ImportError:
    pass

from ansible_collections.ibm.ds8000.plugins.module_utils.ds8000 import (PyDs8k, custom_get_request,
                                   ds8000_argument_spec)

from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule


class HostPortAssigner(PyDs8k):
    def ds8000_assign_host_port(self, host_port):
        self._assign_specific_host_port_to_specific_host(
            host_port)
        return {'changed': self.changed, 'failed': self.failed}

    def _assign_specific_host_port_to_specific_host(self, host_port):
        name = self.params['name']
        if not self.params['force']:
            check_if_wwpn_is_free, the_host_with_desired_host_port = self._does_host_port_bound_to_other_hosts(
                host_port)
            if check_if_wwpn_is_free:
                self.failed = True
                self.module.fail_json(
                    msg="The WWPN {host_port} assigned to another host ({host}) in the storage."
                    " For removing it from its current host and assigning it to its desired host,"
                    " use the force: true parameter.".format(
                        host_port=host_port, host=the_host_with_desired_host_port))
                return
        wwpns = self._get_all_the_host_ports_under_specific_host(name)
        if host_port not in wwpns:
            try:
                self.client.update_host_port_change_host(
                    port_id=host_port, host_name=name)
                self.changed = True
            except pyds8k.exceptions.BadRequest as bad_wwpn:
                self.failed = True
                self.module.fail_json(
                    msg="This WWPN {host_port} not found. "
                    "ERR: {error}".format(
                        host_port=host_port, error=to_native(bad_wwpn)))
            except Exception as generic_exc:
                self.failed = True
                self.module.fail_json(
                    msg="Failed to assign this {host_port} WWPN to the host {host_name}. "
                    "ERR: {error}".format(
                        host_port=host_port,
                        host_name=name,
                        error=to_native(generic_exc)))


    def _does_host_port_bound_to_other_hosts(self, host_port):
        hosts = self.get_ds8000_objects_name_by_type('hosts')
        name = self.params['name']
        for host in hosts:
            if host != name:
                current_host_wwpns = self._get_all_the_host_ports_under_specific_host(
                    host)
                if host_port in current_host_wwpns:
                    return True, host
        return False, None

    def _get_all_the_host_ports_under_specific_host(self, hostname):
        host_ports_url = "/hosts/{host_name}/host_ports".format(
            host_name=hostname)
        response = custom_get_request(self.module, self.headers, host_ports_url)
        parsed_response = json.loads(response.text)['data']['host_ports']
        return [wwpn['wwpn'] for wwpn in parsed_response]


def main():
    argument_spec = ds8000_argument_spec()
    argument_spec.update(
        name=dict(type='str'),
        host_port=dict(type='list', elements='str'),
        force=dict(type='bool', default=False)
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
    )

    pyds8kh = HostPortAssigner(module)

    if pyds8kh.self.does_ds8000_object_exist('name', 'hosts'):
        for host_port in module.params['host_port']:
            host_port = host_port.replace(':', '')
            result = pyds8kh.ds8000_assign_host_port(host_port)
    else:
        pyds8kh.failed = True
        result = {'changed': pyds8kh.changed, 'failed': pyds8kh.failed}

    if result['failed']:
        module.fail_json(**result)
    else:
        module.exit_json(**result)


if __name__ == '__main__':
    main()
