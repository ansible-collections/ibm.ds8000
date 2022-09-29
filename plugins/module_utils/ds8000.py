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
        self.port = module.params['port']
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
        obj = self.does_ds8000_object_exist(function, *args, **kwargs)
        if obj:
            # The returned object should test as True
            return obj
        self.module.fail_json(
            msg="Function: {function}, args: {arguments}, kwargs: {kwarguments} returned no objects on the DS8000 storage system.".format(
                function=function.__name__, arguments=args, kwarguments=json.dumps(kwargs)
            )
        )
        return False

    def does_ds8000_object_exist(self, function, *args, **kwargs):
        try:
            return function(*args, **kwargs)
        except pyds8k.exceptions.NotFound:
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
        if not volume_ids:
            self.failed = True
            self.module.fail_json(msg="Unable to find volume name {volume_name} on the DS8000 storage system.".format(volume_name=volume_name))
        return volume_ids

    def get_resource_group_from_label(self, label):
        resource_groups = self.client.get_resource_groups()
        for resource_group in resource_groups:
            if resource_group.label == label:
                return resource_group
        return None

    def delete_representation_keys(self, representation, key_list=None):
        if key_list:
            for entry in representation:
                for key in key_list:
                    entry.pop(key, None)
        return representation

    def get_ds8000_objects_from_command_output(self, command_output):
        ds8000_objects = []
        if isinstance(command_output, list):
            for obj in command_output:
                representation = obj.representation
                ds8000_objects.append(representation)
        else:
            representation = command_output.representation
            ds8000_objects.append(representation)

        return ds8000_objects

    def connect_to_api(self):
        rest_client = Client(service_address=self.hostname, user=self.username, password=self.password, port=self.port, verify=self.validate_certs)
        return rest_client

    def check_multi_response_results(self, results, item_list=None, item_name='id'):
        # When multiple objects are worked on, the ds8k rest api returns command success even if each object has failed.
        # pyds8k returns an object on success and the dict from the rest api on failure.
        # The rest api dict doesn't specify which object failed, so it can't be identified without tracking the index into the list provided.
        msg = []
        for index, result in enumerate(results):
            item = {}
            item[item_name] = item_list[index] if item_list else "unknown"
            if isinstance(result, dict):
                if result['status'] == 'failed':
                    self.failed = True
                    item['message'] = "Failed. ERR: {code} {message}".format(code=result['code'], message=to_native(result['message']))
                    msg.append(item)
            else:
                item['message'] = "Succeeded."
                msg.append(item)

        if self.failed:
            self.module.fail_json(msg=msg)


def ds8000_argument_spec():
    return dict(
        hostname=dict(type='str', required=True),
        username=dict(type='str', required=True),
        password=dict(type='str', no_log=True, required=True),
        port=dict(type='int', required=False, default=8452),
        validate_certs=dict(type='bool', required=False, default=True),
    )
