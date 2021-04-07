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
        self.headers = {'Content-Type': 'application/json'}
        self.client = connect_to_api(self.module)
        self.token = get_rest_api_token(self.module)

    def _get_all_volumes_on_ds8000_storage(self):
        volumes = []
        pools = self._get_list_of_ds8000_object(DEFAULT_POOLS_URL, 'pools')
        for pool in pools[1]:
            temp_volumes_by_pool = self._get_list_of_ds8000_object(
                '/pools/{pool}/volumes'.format(pool=pool), 'volumes')
            volumes.extend(temp_volumes_by_pool[0])
        return volumes

    def _check_if_ds8000_host_exists(self):
        module = self.module
        name = self.params['name']
        hosts = self._get_all_hosts()
        if name not in hosts:
            module.fail_json(
                msg="The host {name} does not exists on the ds8000 storage.".format(
                    name=name))
            return False
        return True

    def _get_all_hosts(self):
        token = self.token
        hosts = []
        headers = {
            "Content-Type": "application/json",
            "X-Auth-Token": "{token}".format(token=token)
        }
        hosts_url = "/hosts"
        response = costume_get_request(self.module, headers, hosts_url)
        res = json.loads(response.text)
        for host in res['data']['hosts']:
            hosts.append(host['name'])
        return hosts

    def _get_volume_ids_from_name(self, volume_name):
        volume_ids = []
        volumes = self._get_all_volumes_on_ds8000_storage()
        for volume in volumes:
            if volume['name'] == volume_name:
                volume_ids.append(volume['id'])
        return volume_ids

    def _get_list_of_ds8000_object(self, sub_url, ds8000_object):
        token = self.token
        ds8000_objects = []
        ds8000_objects_name = []
        headers = {
            "Content-Type": "application/json",
            "X-Auth-Token": "{token}".format(token=token)
        }
        response = costume_get_request(self.module, headers, sub_url)
        res = json.loads(response.text)
        for obj in res['data']['{obj}'.format(obj=ds8000_object)]:
            ds8000_objects_name.append(obj['name'])
            temp_ds8000_objects_dict = {
                "name": obj['name'],
                "id": obj['id']
            }
            ds8000_objects.append(temp_ds8000_objects_dict)
        return ds8000_objects, ds8000_objects_name


def connect_to_api(module):
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

    restclient = Client(
        service_address=hostname,
        user=username,
        password=password)
    return restclient


def get_rest_api_token(module):
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
        '{schema}://{ip}:{port}{base_url}{auth}'.format(
            schema=schema,
            ip=hostname,
            port=port,
            base_url=DEFAULT_BASE_URL,
            auth=auth_url),
        headers=headers,
        data=data,
        verify=validate_certs)
    if response.status_code == 200:
        token = get_the_rest_api_token_from_the_reponse(response.text)
        return token
    module.fail_json(msg="failed to get the rest api token:"
                         " {response}".format(response=response.text))
    return None


def get_the_rest_api_token_from_the_reponse(response):
    res = json.loads(response)
    return res['token']['token']


def costume_get_request(module, headers, costume_url):
    hostname = module.params['hostname']
    port = module.params['port']
    schema = module.params['http_schema']
    validate_certs = module.params['validate_certs']
    response = requests.get(
        '{schema}://{ip}:{port}{base_url}{costume}'.format(
            schema=schema,
            ip=hostname,
            port=port,
            base_url=DEFAULT_BASE_URL,
            costume=costume_url),
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
