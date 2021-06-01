from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json
import traceback
import abc

from ansible.module_utils.basic import missing_required_lib
from ansible.module_utils.common.text.converters import to_native
from ansible.module_utils import six

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
DEFAULT_POOLS_URL = '/pools'
PRESENT = 'present'
ABSENT = 'absent'


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
        self.token = self.get_rest_api_token()
        self.headers = {'Content-Type': 'application/json'}
        self.token_header = {'X-Auth-Token': '{token}'.format(token=self.token)}
        self.headers.update(self.token_header)
        self.changed = False
        self.failed = False

    def get_all_volumes(self):
        volumes = []
        pools = self.get_ds8000_objects_by_type(DEFAULT_POOLS_URL, 'pools')
        for pool in pools:
            volumes_by_pool = self.get_ds8000_objects_by_type(
                '/pools/{pool}/volumes'.format(pool=pool['name']), 'volumes')
            volumes.extend(volumes_by_pool)
        return volumes

    def verify_ds8000_object_exist(self, ds8000_object_param_name,
                                   ds8000_object_type):
        ds8000_object_name = self.params[ds8000_object_param_name]
        if self.does_ds8000_object_exist(ds8000_object_param_name, ds8000_object_type):
            return True
        self.module.fail_json(
            msg="The {object_type} {object_name} "
                "does not exist in the ds8000 storage.".format(
                    object_type=ds8000_object_type[:-1], object_name=ds8000_object_name))
        return False

    def does_ds8000_object_exist(self, ds8000_object_param_name,
                                 ds8000_object_type):
        ds8000_object_name = self.params[ds8000_object_param_name]
        ds8000_objects = self.get_ds8000_objects_name_by_type(ds8000_object_type)
        return ds8000_object_name in ds8000_objects

    def get_ds8000_objects_name_by_type(self, ds8000_object_type):
        ds8000_object_type_url = "/{object_type}".format(object_type=ds8000_object_type)
        response = self.get_ds8000_object_from_server(ds8000_object_type_url)
        parsed_response = json.loads(response.text)['data']['{object_type}'.format(
            object_type=ds8000_object_type)]
        return [object_type['name'] for object_type in parsed_response]

    def get_volume_ids_from_name(self, volume_name):
        volume_ids = []
        volumes = self.get_all_volumes()
        for volume in volumes:
            if volume['name'] == volume_name:
                volume_ids.append(volume['id'])
        return volume_ids

    def get_ds8000_objects_by_type(self, sub_url, ds8000_object_type):
        ds8000_objects = []
        response = self.get_ds8000_object_from_server(sub_url)
        parsed_response = json.loads(response.text)['data'][ds8000_object_type]
        for obj in parsed_response:
            ds8000_objects.append({
                "name": obj['name'],
                "id": obj['id']
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

    def get_rest_api_token(self):
        port = self.module.params['port']
        schema = self.module.params['http_schema']
        validate_certs = self.module.params['validate_certs']
        auth_url = '/tokens'
        headers = {'Content-Type': 'application/json'}
        data = '{request:{params:{username:' + self.username + ',password:' + self.password + '}}}'

        response = requests.post(
            '{schema}://{hostname}:{port}{base_url}{auth}'.format(
                schema=schema,
                hostname=self.hostname,
                port=port,
                base_url=DEFAULT_BASE_URL,
                auth=auth_url),
            headers=headers,
            data=data,
            verify=validate_certs)
        if response.ok:
            token = self._get_token_from_response(response.text)
            return token
        self.module.fail_json(msg="failed to get the rest api token:"
                                  " {response}".format(response=response.text))
        return None

    def _get_token_from_response(self, response):
        return json.loads(response)['token']['token']

    def get_ds8000_object_from_server(self, ds8000_object_url):
        port = self.module.params['port']
        schema = self.module.params['http_schema']
        validate_certs = self.module.params['validate_certs']
        try:
            response = requests.get(
                '{schema}://{hostname}:{port}{base_url}{custom}'.format(
                    schema=schema,
                    hostname=self.hostname,
                    port=port,
                    base_url=DEFAULT_BASE_URL,
                    custom=ds8000_object_url),
                headers=self.headers,
                verify=validate_certs)
            return response
        except Exception as generic_exc:
            self.module.fail_json(
                msg="Failed to get ds8000 object list from the server"
                    " ERR: {error}".format(
                        error=to_native(generic_exc)))


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
