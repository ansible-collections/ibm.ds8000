# Copyright (C) 2021 IBM CORPORATION
# Author(s): Matan Carmeli <matan.carmeli7@gmail.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import abc
import json
import traceback

from ansible.module_utils import six
from ansible.module_utils.basic import missing_required_lib
from ansible.module_utils.common.text.converters import to_native

REQUESTS_IMP_ERR = None
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    REQUESTS_IMP_ERR = traceback.format_exc()
    HAS_REQUESTS = False

PYDS8K_IMP_ERR = None
try:
    from pyds8k.client.ds8k.v1.client import Client
    HAS_PYDS8K = True
except ImportError:
    PYDS8K_IMP_ERR = traceback.format_exc()
    HAS_PYDS8K = False

DEFAULT_BASE_URL = '/api/v1'
PRESENT = 'present'
ABSENT = 'absent'
BAD_POOL_TYPES = ['ckd']


@six.add_metaclass(abc.ABCMeta)
class Ds8000ManagerBase(object):
    def __init__(self, module):

        if not HAS_REQUESTS:
            module.fail_json(msg=missing_required_lib('requests'),
                             exception=REQUESTS_IMP_ERR)

        if not HAS_PYDS8K:
            module.fail_json(msg=missing_required_lib('pyds8k'),
                             exception=PYDS8K_IMP_ERR)

        self.module = module
        self.params = module.params
        self.hostname = module.params['hostname']
        self.username = module.params['username']
        self.password = module.params['password']
        self.client = self.connect_to_api()
        self.changed = False
        self.failed = False

    def get_all_volumes(self):
        volumes = []
        pools = self.client.get_pools()
        for pool in pools:
            if pool.stgtype not in BAD_POOL_TYPES:
                volumes_by_pool = self.get_ds8000_objects_from_command_output(
                    self.client.get_volumes_by_pool(pool_id=pool.id))
                volumes.extend(volumes_by_pool)
        return volumes

    def verify_ds8000_object_exist(self, ds8000_object_param_name,
                                   command_output):
        ds8000_object_name = self.params[ds8000_object_param_name]
        if self.does_ds8000_object_exist(ds8000_object_param_name, command_output):
            return True
        self.module.fail_json(
            msg="The {object_type} {object_name} "
                "does not exist in the ds8000 storage.".format(
                    object_type=ds8000_object_param_name, object_name=ds8000_object_name))
        return False

    def does_ds8000_object_exist(self, ds8000_object_param_name,
                                 command_output):
        ds8000_object_name = self.params[ds8000_object_param_name]
        ds8000_objects_name = self.get_ds8000_objects_name_from_command_output(command_output)
        ds8000_objects_id = self.get_ds8000_objects_id_from_command_output(command_output)
        return ds8000_object_name in ds8000_objects_name + ds8000_objects_id

    def get_ds8000_objects_name_from_command_output(self, command_output):
        return [object_type.name for object_type in command_output]

    def get_ds8000_objects_id_from_command_output(self, command_output):
        return [object_type.id for object_type in command_output]

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
            ds8000_objects.append({
                "name": obj.name,
                "id": obj.id
            })
        return ds8000_objects

    def connect_to_api(self):
        if not self.hostname:
            self.module.fail_json(msg="Hostname parameter is missing."
                                      " Please specify this parameter in task")

        if not self.username:
            self.module.fail_json(msg="Username parameter is missing."
                                      " Please specify this parameter in task")

        if not self.password:
            self.module.fail_json(msg="Password parameter is missing."
                                      " Please specify this parameter in task")

        rest_client = Client(
            service_address=self.hostname,
            user=self.username,
            password=self.password)
        return rest_client


def ds8000_argument_spec():
    return dict(
        hostname=dict(type='str',
                      required=False),
        username=dict(type='str',
                      required=False),
        password=dict(type='str',
                      no_log=True,
                      required=False),
        port=dict(type='str',
                  required=False,
                  default='8452'),
        validate_certs=dict(type='bool',
                            required=False,
                            default=True),
        http_schema=dict(type='str',
                         required=False,
                         default='https'),
    )
