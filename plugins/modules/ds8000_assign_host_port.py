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
      - The Name of the DS8000 host to work with.
    type: str
  host_port:
    description:
    - list of host_ports to assign to a specific host in DS8000 storage.
    type: list
  force:
    description:
      - If set to True, in a case that a host port is assigned to another host, it will transfer it to the host that specified.
      - If set to False, in case that a host port is assigned to another host, it won't transfer it to the host that specified.
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
    host_port:
      - 10000000C9A1BAB2
      - 10000000C9A1BAB3

- name: Assign some host ports to host with force on true
  ibm.ds8000.ds8000_assign_host_port:
    hostname: "{{ ds8000_host }}"
    username: "{{ ds8000_username }}"
    password: "{{ ds8000_password }}"
    name: host_name_test
    host_port: 10000000C9A1BAB2
'''

RETURN = r''' # '''

import json

try:
    import pyds8k.exceptions
except ImportError:
    pass

from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule

from ..module_utils.ds8000 import (PyDs8k, costume_get_request,
                                   ds8000_argument_spec)


class PyDs8kHelper(PyDs8k):
    def __init__(self, module):
        super(PyDs8kHelper, self).__init__(module)
        self.changed = False
        self.failed = False

    def _ds8000_assign_host_port(self, host_port):
        result = {}
        name = self.params['name']
        changed, failed = self._assign_specific_host_port_to_specific_host(
            host_port)
        result = {'changed': changed, 'failed': failed}
        return result

    def _assign_specific_host_port_to_specific_host(self, host_port):
        name = self.params['name']
        client = self.client
        if not self.params['force']:
            check_if_wwpn_is_free, the_host_with_the_desired_host_port = self._check_if_the_host_port_is_free(
                host_port)
            if check_if_wwpn_is_free:
                self.failed = True
                self.module.fail_json(
                    msg="The WWPN {host_port} assiened to another host ({host}) in the storage.\n"
                    "For removing it from his current host and moving it to his desired host,"
                    "use the force: true parameter.".format(
                        host_port=host_port, host=the_host_with_the_desired_host_port))
                return self.changed, self.failed
        wwpns = self._get_all_the_host_ports_under_specific_host(name)
        if host_port not in wwpns:
            try:
                client.update_host_port_change_host(
                    port_id=host_port, host_name=name)
                self.changed = True
            except pyds8k.exceptions.BadRequest as bad_wwpn:
                self.failed = True
                if ':' in host_port:
                    self.module.fail_json(
                        msg="This WWPN {host_port} not found, remove ':' from the WWPN. "
                        "bad WWPN: 10:00:00:00:C9:A1:BA:B2 "
                        "good WWPN: 10000000C9A1BAB2. "
                        "ERR: {error}".format(
                            host_port=host_port,
                            error=to_native(bad_wwpn)))
                else:
                    self.module.fail_json(
                        msg="This WWPN {host_port} not found. "
                        "ERR: {error}".format(
                            host_port=host_port, error=to_native(bad_wwpn)))
            except Exception as generic_exc:
                self.failed = True
                self.module.fail_json(
                    msg="can't assign this {host_port} WWPN to the host {host_name}. "
                    "ERR: {error}".format(
                        host_port=host_port,
                        host_name=name,
                        error=to_native(generic_exc)))

        return self.changed, self.failed

    def _check_if_the_host_port_is_free(self, host_port):
        hosts = self._get_all_hosts()
        name = self.params['name']
        for host in hosts:
            if host != name:
                current_host_wwpns = self._get_all_the_host_ports_under_specific_host(
                    host)
                if host_port in current_host_wwpns:
                    return True, host
        return False, None

    def _get_all_the_host_ports_under_specific_host(self, hostname):
        token = self.token
        wwpns = []
        headers = {
            "Content-Type": "application/json",
            "X-Auth-Token": "{token}".format(token=token)
        }
        host_ports_url = "/hosts/{host_name}/host_ports".format(
            host_name=hostname)
        response = costume_get_request(self.module, headers, host_ports_url)
        res = json.loads(response.text)
        for host_port in res['data']['host_ports']:
            wwpns.append(host_port['wwpn'])
        return wwpns


def main():
    argument_spec = ds8000_argument_spec()
    argument_spec.update(
        name=dict(type='str'),
        host_port=dict(type='list'),
        force=dict(type='bool', default=False)
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
    )

    pds8kh = PyDs8kHelper(module)

    if not pds8kh._check_if_ds8000_host_exists():
        result = {'changed': False, 'failed': True}
    else:
        for host_port in module.params['host_port']:
            result = pds8kh._ds8000_assign_host_port(host_port)

    if 'failed' not in result:
        result['failed'] = False

    if result['failed']:
        module.fail_json(**result)
    else:
        module.exit_json(**result)


if __name__ == '__main__':
    main()
