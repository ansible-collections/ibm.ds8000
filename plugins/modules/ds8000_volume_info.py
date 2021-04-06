#! /usr/bin/python

from __future__ import absolute_import, division, print_function

__metaclass__ = type

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
            _, hosts = self._get_list_of_ds8000_object(
                DEFAULT_HOSTS_URL, 'hosts')
            if self.params['host'] in hosts:
                volumes_by_host, _ = self._get_list_of_ds8000_object(
                    '/hosts/{}/volumes'.format(self.params['host']), 'volumes')
            else:
                self.module.fail_json(
                    msg="The host {} is not exists".format(
                        self.params['host']))
        if self.params['pool']:
            _, pools = self._get_list_of_ds8000_object(
                DEFAULT_POOLS_URL, 'pools')
            if self.params['pool'] in pools:
                volumes_by_pool, _ = self._get_list_of_ds8000_object(
                    '/pools/{}/volumes'.format(self.params['pool']), 'volumes')
            else:
                self.module.fail_json(
                    msg="The pool {} is not exists".format(
                        self.params['pool']))
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
