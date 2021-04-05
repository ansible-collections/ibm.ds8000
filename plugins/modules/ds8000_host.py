#!/usr/bin/python

from __future__ import division, print_function

__metaclass__ = type

from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule

from ..module_utils.ds8000 import (
    PyDs8k, ds8000_argument_spec)


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
                self.module.fail_json(msg="Failed to add {} host to the DS8000 storage.".format(name),
                                      detail=generic_exc)
        return changed, failed

    def _check_if_the_host_exists(self):
        name = self.params['name']
        client = self.client
        try:
            client.get_host(host_name=name)
            return True
        except:
            return False

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
                self.module.fail_json(msg="Failed to remove {} host from the DS8000 storage. ERR: {}".format(name, to_native(generic_exc))
        return changed, failed

def main():
    argument_spec=ds8000_argument_spec()
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

    module=AnsibleModule(
        argument_spec=argument_spec,
    )

    pds8kh=PyDs8kHelper(module)

    if module.params['state'] == 'present':
        result=pds8kh._ds8000_host_present()
    elif module.params['state'] == 'absent':
        result=pds8kh._ds8000_host_absent()

    if 'failed' not in result:
        result['failed']=False

    if result['failed']:
        module.fail_json(**result)
    else:
        module.exit_json(**result)


if __name__ == '__main__':
    main()
