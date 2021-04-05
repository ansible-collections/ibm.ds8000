#!/usr/bin/python

from __future__ import division, print_function

__metaclass__ = type

import json
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native

import pyds8k.exceptions
from ..module_utils.ds8000 import (
    PyDs8k, ds8000_argument_spec, costume_get_request)


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
                    msg="The WWPN {} assiened to another host ({}) in the storage.\n"
                    "For removing it from his current host and moving it to his desired host,"
                    "use the force: true parameter.".format(
                        host_port, the_host_with_the_desired_host_port))
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
                        msg="This WWPN {} not found, remove ':' from the WWPN. "
                        "bad WWPN: 10:00:00:00:C9:A1:BA:B2 "
                        "good WWPN: 10000000C9A1BAB2. "
                        "ERR: {}".format(
                            host_port, to_native(bad_wwpn)))
                else:
                    self.module.fail_json(
                        msg="This WWPN {} not found. "
                        "ERR: {}".format(
                            host_port, to_native(bad_wwpn)))
            except Exception as generic_exc:
                self.failed = True
                self.module.fail_json(
                    msg="can't assign this {} WWPN to the host {}. "
                    "ERR: {}".format(
                        host_port, name, to_native(generic_exc)))

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
            "X-Auth-Token": "{}".format(token)
        }
        host_ports_url = "/hosts/{}/host_ports".format(hostname)
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
