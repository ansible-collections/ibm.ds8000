from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json
import traceback

from ansible.module_utils.basic import missing_required_lib

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


class PyDs8k(object):
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

    def get_all_volumes_in_ds8000_storage(self):
        volumes = []
        pools = self.get_ds8000_objects_by_type(DEFAULT_POOLS_URL, 'pools')
        for pool in pools:
            volumes_by_pool = self.get_ds8000_objects_by_type(
                '/pools/{pool}/volumes'.format(pool=pool['name']), 'volumes')
            volumes.extend(volumes_by_pool)
        return volumes

    def does_ds8000_object_exist(self, ds8000_object_param_name, ds8000_object_type, fail_on_not_exists=True):
        module = self.module
        ds8000_object_name = self.params[ds8000_object_param_name]
        ds8000_objects = self.get_ds8000_objects_name_by_type(ds8000_object_type)
        if ds8000_object_name not in ds8000_objects:
            if fail_on_not_exists:
                module.fail_json(
                    msg="The {object_type} {object_name} does not exists in the ds8000 storage.".format(
                        object_type=ds8000_object_type[:-1], object_name=ds8000_object_name))
            return False
        return True

    def get_ds8000_objects_name_by_type(self,ds8000_object_type):
        ds8000_object_type_url = "/{object_type}".format(object_type=ds8000_object_type)
        response = custom_get_request(self.module, self.headers, ds8000_object_type_url)
        parsed_response = json.loads(response.text)['data']['{object_type}'.format(object_type=ds8000_object_type)]
        return [object_type['name'] for object_type in parsed_response]

    def get_volume_ids_from_name(self, volume_name):
        volume_ids = []
        volumes = self.get_all_volumes_in_ds8000_storage()
        for volume in volumes:
            if volume['name'] == volume_name:
                volume_ids.append(volume['id'])
        return volume_ids

    def get_ds8000_objects_by_type(self, sub_url, ds8000_object_type):
        ds8000_objects = []
        response = custom_get_request(self.module, self.headers, sub_url)
        parsed_response = json.loads(response.text)['data'][ds8000_object_type]
        for obj in parsed_response:
            ds8000_objects.append({
                "name": obj['name'],
                "id": obj['id']
            })
        return ds8000_objects


    def connect_to_api(self):
        module = self.module
        hostname = module.params['hostname']
        username = module.params['username']
        password = module.params['password']
    
        if not hostname:
            module.fail_json(msg="Hostname parameter is missing."
                                 " Please specify this parameter in task")
    
        if not username:
            module.fail_json(msg="Username parameter is missing."
                                 " Please specify this parameter in task")
    
        if not password:
            module.fail_json(msg="Password parameter is missing."
                                 " Please specify this parameter in task")
    
        rest_client = Client(
            service_address=hostname,
            user=username,
            password=password)
        return rest_client
    
    
    def get_rest_api_token(self):
        module = self.module
        hostname = module.params['hostname']
        username = module.params['username']
        password = module.params['password']
        port = module.params['port']
        schema = module.params['http_schema']
        validate_certs = module.params['validate_certs']
        auth_url = '/tokens'
        headers = {'Content-Type': 'application/json'}
        data = '{request:{params:{username:' + username + ',password:' + password + '}}}'
    
        response = requests.post(
            '{schema}://{hostname}:{port}{base_url}{auth}'.format(
                schema=schema,
                hostname=hostname,
                port=port,
                base_url=DEFAULT_BASE_URL,
                auth=auth_url),
            headers=headers,
            data=data,
            verify=validate_certs)
        if response.ok:
            token = get_the_rest_api_token_from_the_reponse(response.text)
            return token
        module.fail_json(msg="failed to get the rest api token:"
                             " {response}".format(response=response.text))
        return None


def get_the_rest_api_token_from_the_reponse(response):
    return json.loads(response)['token']['token']


def custom_get_request(module, headers, custom_url):
    hostname = module.params['hostname']
    port = module.params['port']
    schema = module.params['http_schema']
    validate_certs = module.params['validate_certs']
    response = requests.get(
        '{schema}://{ip}:{port}{base_url}{custom}'.format(
            schema=schema,
            ip=hostname,
            port=port,
            base_url=DEFAULT_BASE_URL,
            custom=custom_url),
        headers=headers,
        verify=validate_certs)
    return response


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
