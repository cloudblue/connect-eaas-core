## Create the Anvil application class

Now it's time to create our python module that will contain our events application:

```
$ touch tshirt_extension/anvilapp.py
```

Open the `tshirt_extension/anvilapp.py` with your favorite editor and put the following content inside it:

```python hl_lines="1 4"
from connect.eaas.core.extension import AnvilApplicationBase


class TShirtAnvilApplication(AnvilApplicationBase):
    pass
```

## Declare the Anvil application class in your pyproject.toml file

Your extension will be executed by the EaaS runtime called [Connect Extension Runner](https://github.com/cloudblue/connect-extension-runner).

The runner uses setuptools entrypoints to discover the features that your extensions implements, so we have to modify our **pyproject.toml** add an entrypoint for our Anvil application:


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


## Declare the environment variable that will store the Anvil Uplink key

The Anvil Uplink Server needs an authentication key to communicate with the Anvil Client Application.
This key must be stored as a secure environment variable. Using the `@anvil_key_variable` decorator, 
the variable will be created on the first run of the extension and you have just to edit its value
and put a valid Anvil Uplink key: 



```python hl_lines="1 5"
from connect.eaas.core.decorators import anvil_key_variable
from connect.eaas.core.extension import AnvilApplicationBase


@anvil_key_variable('ANVIL_UPLINK_KEY')
class TShirtAnvilApplication(AnvilApplicationBase):
    pass
```

## Declare environment variables to store the marketplace id and the connection id.

To create a purchase request you will need to specify the marketplace from which
this purchase request is coming from as long as the connection id of the connection
between the product and the hub from which the purchase request will come from:


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



## Create an Anvil callable to retrieve product information

Let's create an Anvil callable that given a product id as the call argument
it returns the product JSON representation to fill the Anvil Client form:


```python hl_lines="1 19-21"
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
```

## Add a static method to generate the purchase request payload

Now let's create a static method that help in generating the
purchase request payload:

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


## Create an Anvil callable to send the purchase request to Connect

Finally create an Anvil callable that send the purchase to Connect:

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
    :partying_face: your first `Anvil Application` is ready to be tested :beers:
