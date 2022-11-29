## Create the Anvil application class

Define a python module that includes your application type. The following showcases how to create a module that implements an anvil application:

```
$ touch tshirt_extension/anvilapp.py
```

Open the `tshirt_extension/anvilapp.py` with your code editor and provide the following data:

```python hl_lines="1 4"
from connect.eaas.core.extension import AnvilApplicationBase


class TShirtAnvilApplication(AnvilApplicationBase):
    pass
```

## Add anvil application class in `pyproject.toml`

Your hub integration extension will be executed by the EaaS runtime called [Connect Extension Runner](https://github.com/cloudblue/connect-extension-runner).

This runner uses setuptools entrypoints to discover features that are provided by your extensions. Thus, it is required to modify the **pyproject.toml** file and add an entrypoint for your Anvil application:


```toml hl_lines="13 14"
[tool.poetry]
name = "tshirt-extension"
version = "0.1.0"
description = "T-Shirt extension"
authors = ["Globex corporation"]
readme = "README.md"
packages = [{include = "tshirt_extension"}]

[tool.poetry.dependencies]
python = ">=3.8,<3.11"
connect-eaas-core = ">=26.12,<27"

[tool.poetry.plugins."connect.eaas.ext"]
"anvilapp" = "tshirt_extension.anvilapp:TShirtAnvilApplication"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```


## Define Anvil Uplink key variable

The Anvil Uplink Server requires an authentication key to communicate with your Anvil Client application.
This key must be stored as a secure environment variable. 

By using the `@anvil_key_variable` decorator, this variable will be created during the first launch of your extension. 
Thereafter, you can edit its value and prove a valid Anvil Uplink key: 



```python hl_lines="1 5"
from connect.eaas.core.decorators import anvil_key_variable
from connect.eaas.core.extension import AnvilApplicationBase


@anvil_key_variable('ANVIL_UPLINK_KEY')
class TShirtAnvilApplication(AnvilApplicationBase):
    pass
```

## Declare Marketplace and Connection variables.

In order to create a purchase request, it is required declare environment variables for marketplace and connection identifiers from the Connect platform. 
These identifers are used to select your required marketplace and connection between your product and your hub. Thus, this allows locating the source of your generated purchase requests. Declare these variables as follows:


```python hl_lines="1 5-16"
from connect.eaas.core.decorators import anvil_key_variable, variables
from connect.eaas.core.extension import AnvilApplicationBase


@variables(
    [
        {
            'name': 'MARKETPLACE_ID',
            'initial_value': '<change_me>',
        },
        {
            'name': 'CONNECTION_ID',
            'initial_value': '<change_me>',
        },
    ],
)
@anvil_key_variable('ANVIL_UPLINK_KEY')
class TShirtAnvilApplication(AnvilApplicationBase):
    pass
```



## Define Anvil callable for product data

Create an Anvil callable to retrieve product information. Specifically, it should receive a product ID as an argument
and return your product JSON data that is subsequently used to fill the Anvil Client form. Define this callable as follows:


```python hl_lines="1 19-21"
from connect.eaas.core.decorators import anvil_key_variable, anvil_callable, variables
from connect.eaas.core.extension import AnvilApplicationBase
an argiment

@variables(
    [
        {
            'name': 'MARKETPLACE_ID',
            'initial_value': '<change_me>',
        },
        {
            'name': 'CONNECTION_ID',
            'initial_value': '<change_me>',
        },
    ],
)
@anvil_key_variable('ANVIL_UPLINK_KEY')
class TShirtAnvilApplication(AnvilApplicationBase):
    @anvil_callable()
    def retrieve_product(self, product_id):
        return self.client.products[product_id].get()
```

## Add static method for purchase request payload

Create a static method that will be used to generate a purchase request payload. 
Declare this method as follows:

``` python hl_lines="1 25-106"
from uuid import uuid4

from connect.eaas.core.decorators import anvil_key_variable, anvil_callable, variables
from connect.eaas.core.extension import AnvilApplicationBase


@variables(
    [
        {
            'name': 'MARKETPLACE_ID',
            'initial_value': '<change_me>',
        },
        {
            'name': 'CONNECTION_ID',
            'initial_value': '<change_me>',
        },
    ],
)
@anvil_key_variable('ANVIL_UPLINK_KEY')
class TShirtAnvilApplication(AnvilApplicationBase):
    @anvil_callable()
    def retrieve_product(self, product_id):
        return self.client.products[product_id].get()

    @staticmethod
    def create_request_payload(product_id, size, quantity):
        asset_uuid = str(uuid4())
        return {
            'type': 'purchase',
            'status': 'pending',
            'asset': {
                'product': {
                    'id': product_id
                },
                'connection': {
                    'id': self.config['CONNECTION_ID'],
                },
                'external_uid': asset_uuid,
                'external_id': asset_uuid,
                'items': [
                    {
                        'quantity': quantity,
                        'global_id': f'{product_id}-0001'
                    },
                ],
                'params': [
                    {
                        'id': 'size',
                        'value': size,
                    }
                ],
                'tiers': {
                    'customer': {
                        'name': 'Super Company IT INC',
                        'external_id': '19065',
                        'external_uid': '99432fdb-8363-4843-abfc-cd0a0854a65a',
                        'contact_info': {
                            'address_line1': 'Bernhard Crossing',
                            'address_line2': 'Myrtice Viaduct',
                            'city': 'Balgowlah',
                            'state': 'Balgowlah',
                            'postal_code': '2093',
                            'country': 'AU',
                            'contact': {
                                'first_name': 'Jeff',
                                'last_name': 'Erdman',
                                'email': 'test.user+Jeff_Erdman@ingrammicro.com',
                                'phone_number': {
                                    'country_code': '+61',
                                    'area_code': '255',
                                    'phone_number': '54004',
                                    'extension': '',
                                }
                            }
                        }
                    },
                    'tier1': {
                        'name': 'Super Tier 1',
                        'external_id': '19066',
                        'external_uid': '99432fdb-8363-4843-abfc-cd0a0854a65b',
                        'contact_info': {
                            'address_line1': 'Bernhard Crossing',
                            'address_line2': 'Myrtice Viaduct',
                            'city': 'Balgowlah',
                            'state': 'Balgowlah',
                            'postal_code': '2093',
                            'country': 'AU',
                            'contact': {
                                'first_name': 'Jeff',
                                'last_name': 'Erdman',
                                'email': 'test.user+Jeff_Erdman@ingrammicro.com',
                                'phone_number': {
                                    'country_code': '+61',
                                    'area_code': '255',
                                    'phone_number': '54004',
                                    'extension': '',
                                }
                            }
                        }
                    },
                },
            },
            'marketplace': {
                'id': self.config['CONNECTION_ID'],
            },
        }
```


## Create Anvil callable to send requests

Finally, create an Anvil callable that sends purchase requests to the Connect platform.
Declare this callable as follows:

``` python hl_lines="25-33"
from uuid import uuid4

from connect.eaas.core.decorators import anvil_key_variable, anvil_callable, variables
from connect.eaas.core.extension import AnvilApplicationBase


@variables(
    [
        {
            'name': 'MARKETPLACE_ID',
            'initial_value': '<change_me>',
        },
        {
            'name': 'CONNECTION_ID',
            'initial_value': '<change_me>',
        },
    ],
)
@anvil_key_variable('ANVIL_UPLINK_KEY')
class TShirtAnvilApplication(AnvilApplicationBase):
    @anvil_callable()
    def retrieve_product(self, product_id):
        return self.client.products[product_id].get()

    @anvil_callable()
    def buy_now(self, product_id, size, quantity):
        payload = TShirtAnvilApplication.create_request_payload(
            product_id,
            size,
            quantity,
        )
        request = self.client.requests.create(payload=payload)
        return request['id']

    @staticmethod
    def create_request_payload(product_id, size, quantity):
        asset_uuid = str(uuid4())
        return {
            'type': 'purchase',
            'status': 'pending',
            'asset': {
                'product': {
                    'id': product_id
                },
                'connection': {
                    'id': self.config['CONNECTION_ID'],
                },
                'external_uid': asset_uuid,
                'external_id': asset_uuid,
                'items': [
                    {
                        'quantity': quantity,
                        'global_id': f'{product_id}-0001'
                    },
                ],
                'params': [
                    {
                        'id': 'size',
                        'value': size,
                    }
                ],
                'tiers': {
                    'customer': {
                        'name': 'Super Company IT INC',
                        'external_id': '19065',
                        'external_uid': '99432fdb-8363-4843-abfc-cd0a0854a65a',
                        'contact_info': {
                            'address_line1': 'Bernhard Crossing',
                            'address_line2': 'Myrtice Viaduct',
                            'city': 'Balgowlah',
                            'state': 'Balgowlah',
                            'postal_code': '2093',
                            'country': 'AU',
                            'contact': {
                                'first_name': 'Jeff',
                                'last_name': 'Erdman',
                                'email': 'test.user+Jeff_Erdman@ingrammicro.com',
                                'phone_number': {
                                    'country_code': '+61',
                                    'area_code': '255',
                                    'phone_number': '54004',
                                    'extension': '',
                                }
                            }
                        }
                    },
                    'tier1': {
                        'name': 'Super Tier 1',
                        'external_id': '19066',
                        'external_uid': '99432fdb-8363-4843-abfc-cd0a0854a65b',
                        'contact_info': {
                            'address_line1': 'Bernhard Crossing',
                            'address_line2': 'Myrtice Viaduct',
                            'city': 'Balgowlah',
                            'state': 'Balgowlah',
                            'postal_code': '2093',
                            'country': 'AU',
                            'contact': {
                                'first_name': 'Jeff',
                                'last_name': 'Erdman',
                                'email': 'test.user+Jeff_Erdman@ingrammicro.com',
                                'phone_number': {
                                    'country_code': '+61',
                                    'area_code': '255',
                                    'phone_number': '54004',
                                    'extension': '',
                                }
                            }
                        }
                    },
                },
            },
            'marketplace': {
                'id': self.config['CONNECTION_ID'],
            },
        }
```


!!! success "Congratulations"
    :partying_face: Your `Anvil Application` should be ready for the following tests :beers:
