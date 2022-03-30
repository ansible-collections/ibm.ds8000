# Copyright (C) 2021 IBM CORPORATION
# Apache License, Version 2.0 (see https://opensource.org/licenses/Apache-2.0)

'''Python versions supported: >= 3.6'''

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import abc
import json
import traceback

from ansible.module_utils import six
from ansible.module_utils.basic import missing_required_lib
from ansible.module_utils.common.text.converters import to_native

PYDS8K_IMP_ERR = None
try:
    from pyds8k.client.ds8k.v1.client import Client

    HAS_PYDS8K = True
except ImportError:
    PYDS8K_IMP_ERR = traceback.format_exc()
    HAS_PYDS8K = False

try:
    import pyds8k.exceptions
except ImportError:
    pass

DEFAULT_BASE_URL = '/api/v1'
PRESENT = 'present'
ABSENT = 'absent'


@six.add_metaclass(abc.ABCMeta)
class Ds8000ManagerBase(object):
    def __init__(self, module):

        if not HAS_PYDS8K:
            module.fail_json(msg=missing_required_lib('pyds8k'), exception=PYDS8K_IMP_ERR)

        self.module = module
        self.params = module.params
        self.hostname = module.params['hostname']
        self.username = module.params['username']
        self.password = module.params['password']
        self.validate_certs = module.params['validate_certs']
        self.client = self.connect_to_api()
        self.changed = False
        self.failed = False

    def get_all_volumes(self):
        volumes = []
        pools = self.client.get_pools()
        for pool in pools:
            volumes_by_pool = self.get_ds8000_objects_from_command_output(self.client.get_volumes_by_pool(pool_id=pool.id))
            volumes.extend(volumes_by_pool)
        return volumes

    def verify_ds8000_object_exist(self, function, *args, **kwargs):
        if self.does_ds8000_object_exist(function, *args, **kwargs):
            return True
        self.module.fail_json(
            msg="Function: {function}, args: {arguments}, kwargs: {kwarguments} returned no objects on the DS8000 storage system.".format(
                function=function.__name__, arguments=args, kwarguments=json.dumps(kwargs)
            )
        )
        return False

    def does_ds8000_object_exist(self, function, *args, **kwargs):
        try:
            return function(*args, **kwargs)
        except pyds8k.exceptions.NotFound as generic_exc:
            return None
        except Exception as generic_exc:
            self.failed = True
            self.module.fail_json(msg="Function {function} exception." "ERR: {error}".format(function=function.__name__, error=to_native(generic_exc)))

    def get_volume_ids_from_name(self, volume_name):
        volume_ids = []
        volumes = self.get_all_volumes()
        for volume in volumes:
            if volume['name'] == volume_name:
                volume_ids.append(volume['id'])
        return volume_ids

    def get_ds8000_objects_from_command_output(self, command_output):
        ds8000_objects = []
        for obj in command_output:
            ds8000_objects.append({"name": obj.name, "id": obj.id})
        return ds8000_objects

    def connect_to_api(self):
        rest_client = Client(service_address=self.hostname, user=self.username, password=self.password, verify=self.validate_certs)
        return rest_client


def ds8000_argument_spec():
    return dict(
        hostname=dict(type='str', required=True),
        username=dict(type='str', required=True),
        password=dict(type='str', no_log=True, required=True),
        port=dict(type='str', required=False, default='8452'),
        validate_certs=dict(type='bool', required=False, default=True),
    )
