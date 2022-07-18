# IBM DS8000 Collection for Ansible

<!-- Add CI and code coverage badges here. Samples included below. -->

[![CI](https://github.com/ansible-collections/ibm.ds8000/workflows/CI/badge.svg?event=push)](https://github.com/ansible-collections/ibm.ds8000/actions/workflows/ansible-test.yml)
[![Codecov](https://img.shields.io/codecov/c/github/ansible-collections/ibm.ds8000)](https://codecov.io/gh/ansible-collections/ibm.ds8000)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

<!-- Describe the collection and why a user would want to use it. What does the collection do? -->

This collection provides a series of Ansible modules and plugins for interacting with the IBM DS8000 family storage products. For more information regarding these products, see [IBM Documentation](https://www.ibm.com/docs/en).

## Tested with Ansible

<!-- List the versions of Ansible the collection has been tested with. Must match what is in galaxy.yml. -->

Tested with the current Ansible 2.9, 2.10, 2.11, 2.12 releases and the current development version of Ansible. Ansible versions before 2.9.10 are not supported.

## Python Requirements

This collection supports Python versions >=3.6 as required by pyds8k.

## External requirements

<!-- List any external resources the collection depends on, for example minimum versions of an OS, libraries, or utilities. Do not list other Ansible collections here. -->

| Name               | Minimum Version                        |
| ------------------ | -------------------------------------- |
| pyds8k             | v1.4.0                                 |
| IBM DS8000® family | 8.x and higher with same API interface |

## Included content

<!-- Galaxy will eventually list the module docs within the UI, but until that is ready, you may need to either describe your plugins etc here, or point to an external docsite to cover that information. -->

### Modules

| Name                  | Description                           |
| --------------------- | ------------------------------------- |
| ds8000_host_port      | Manage host ports for a DS8000 host   |
| ds8000_host_port_info | Return info on DS8000 host ports      |
| ds8000_host           | Manage DS8000 hosts                   |
| ds8000_host_info      | Return info on DS8000 hosts           |
| ds8000_lss_info       | Return info on DS8000 lsses           |
| ds8000_marray_info    | Return info on DS8000 managed arrays  |
| ds8000_pool_info      | Return info on DS8000 pools           |
| ds8000_volume_info    | Return basic info on DS8000 volumes   |
| ds8000_volume_mapping | Manage DS8000 volume mapping to hosts |
| ds8000_volume         | Manage DS8000 volumes                 |
| ds8000_lss            | Manage DS8000 lsses                   |

## Idempotency

Modules are idempotent except where noted.

## Using this collection

<!--Include some quick examples that cover the most common use cases for your collection content. It can include the following examples of installation and upgrade (change NAMESPACE.COLLECTION_NAME correspondingly):-->

### Installing the Collection from Ansible Galaxy

Before using this collection, you need to install it with the Ansible Galaxy command-line tool:

```bash
ansible-galaxy collection install ibm.ds8000
```

You can also include it in a `requirements.yml` file and install it with `ansible-galaxy collection install -r requirements.yml`, using the format:

```yaml
---
collections:
  - name: ibm.ds8000
```

Note that if you install the collection from Ansible Galaxy, it will not be upgraded automatically when you upgrade the `ansible` package. To upgrade the collection to the latest available version, run the following command:

```bash
ansible-galaxy collection install ibm.ds8000 --upgrade
```

You can also install a specific version of the collection, for example, if you need to downgrade when something is broken in the latest version (please report an issue in this repository). Use the following syntax to install version `0.1.0`:

```bash
ansible-galaxy collection install ibm.ds8000:==0.1.0
```

### Configuring Trusted Communication

Trusted communication with the IBM DS8000 over HTTPS is controlled by the collection variable `validate_certs`. The default `yes` validates the SSL chain of trust. To complete the chain of trust, the public certificates for the certificate authorities whom signed the IBM DS8000 Communications Certificate must be added to the trust store. This collection uses the Python library pyds8k, which uses the [requests](https://docs.python-requests.org/) library whom uses [certifi](https://certifiio.readthedocs.io/en/latest/).

1. Find the version of python used by ansible (using jq to parse the json output):

   ```bash
   ansible localhost -m ansible.builtin.setup | sed '1c {' | jq '.ansible_facts.ansible_python.executable'
   ```

2. Find the location of the trust store file used by requests:

   ```bash
   python -c "import requests;print(requests.certs.where())"
   ```

3. Append the CA certificate (in PEM format) to the certifi trust store file:

   ```bash
   cat ca_public_certificate.pem >> /usr/local/lib/python3.6/site-packages/certifi/cacert.pem
   ```

To disable validation, set the collection variable `validate_certs=no`.

### Example Playbook

```yaml
---
- name: Using the IBM DS8000 collection
  hosts: localhost
  # Define common module parameters
  module_defaults:
    # ansible-core  < 2.11 - define for each module
    # ibm.ds8000.ds8000_volume:
    # ansible-core >= 2.12 - use module defaults group for all modules
    group/ibm.ds8000.ds8000:
      hostname: "{{ hostname }}"
      username: "{{ username }}"
      password: "{{ password }}"
      validate_certs: no
  tasks:
    - name: Create fb volume
      ibm.ds8000.ds8000_volume:
        name: ansible
        state: present
        pool: P0
        capacity: "1"
      register: create
    - name: Delete fb volume
      ibm.ds8000.ds8000_volume:
        volume_id: "{{ item.id }} "
        state: absent
      with_items: "{{ create.volumes }}"
```

See [Ansible Using collections](https://docs.ansible.com/ansible/devel/user_guide/collections_using.html) for more details.

## Contributing to this collection

<!--Describe how the community can contribute to your collection. At a minimum, include how and where users can create issues to report problems or request features for this collection.  List contribution requirements, including preferred workflows and necessary testing, so you can benefit from community PRs. If you are following general Ansible contributor guidelines, you can link to - [Ansible Community Guide](https://docs.ansible.com/ansible/latest/community/index.html). -->

Currently we are not accepting community contributions. Though, you may periodically review this content to learn when and how contributions can be made in the future.

### Code Style

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Arguments

```shell
  --line-length=160
  --skip-string-normalization
```

## Release notes

See the [changelog](https://github.com/ansible-collections/ibm.ds8000/tree/main/CHANGELOG.rst).

## More information

<!-- List out where the user can find additional information, such as working group meeting times, slack/IRC channels, or documentation for the product this collection automates. At a minimum, link to: -->

- [Ansible Collection overview](https://github.com/ansible-collections/overview)
- [Ansible User guide](https://docs.ansible.com/ansible/latest/user_guide/index.html)
- [Ansible Developer guide](https://docs.ansible.com/ansible/latest/dev_guide/index.html)
- [Ansible Collections Checklist](https://github.com/ansible-collections/overview/blob/master/collection_requirements.rst)
- [Ansible Community code of conduct](https://docs.ansible.com/ansible/latest/community/code_of_conduct.html)
- [The Bullhorn (the Ansible Contributor newsletter)](https://us19.campaign-archive.com/home/?u=56d874e027110e35dea0e03c1&id=d6635f5420)
- [Changes impacting Contributors](https://github.com/ansible-collections/overview/issues/45)
- [IBM Documentation](https://www.ibm.com/docs/en/ds8900)

## Licensing

<!-- Include the appropriate license information here and a pointer to the full licensing details. If the collection contains modules migrated from the ansible/ansible repo, you must use the same license that existed in the ansible/ansible repo. See the GNU license example below. -->

Apache License, Version 2.0

See [LICENSE](https://opensource.org/licenses/Apache-2.0) to see the full text.
