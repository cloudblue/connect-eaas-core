## Requirements

To complete this tutorial you need:

* Python 3.8, 3.9 or 3.10
* [Docker](https://www.docker.com/)
* Latest release of [Poetry](https://python-poetry.org/)


## Bootstrap project

Let's start creating a pyproject.toml file with the base information about your extension project:


```
$ mkdir tshirt_extension
$ cd tshirt_extension
$ poetry init --name tshirt-extension --description "T-Shirt extension" --author "Globex corporation" --python ">=3.8,<3.11" --dependency="connect-eaas-core>={{ core_version() }},<{{ next_major() }}" --no-interaction
```

The `poetry init` command will create the following pyproject.toml file:

```
[tool.poetry]
name = "tshirt-extension"
version = "0.1.0"
description = "T-Shirt extension"
authors = ["Globex corporation"]
readme = "README.md"
packages = [{include = "tshirt_extension"}]

[tool.poetry.dependencies]
python = ">=3.8,<3.11"
connect-eaas-core = ">={{ core_version() }},<{{ next_major() }}"


[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

Now let's create the root python package of your project, a readme file and a changelog file:

```
$ mkdir tshirt_extension
$ touch README.md
$ touch CHANGELOG.md
```

## Create the extension project descriptor file

First of all creates an empty descriptor file inside your extension root package:

```
$ touch tshirt_extension/extension.json
```

!!! note
    The name of the descriptor file must be **extension.json** and must be located inside the root package of your extension project.


Assuming that your extension code will be hosted on **github.com** under the account `myaccount` and the repository name `tshirt_extension`, open the extension.json file using your favorite editor and fill it with:

```
{
    "name": "tshirt",
    "description": "This extension allows create a purchase order for a t-shirt using an Anvil Client Application.",
    "version": "1.0.0",
    "audience": ["distributor"],
    "readme_url": "https://raw.githubusercontent.com/myaccount/tshirt_extension/master/README.md",
    "changelog_url": "https://raw.githubusercontent.com/myaccount/tshirt_extension/master/CHANGELOG.md"
}
```

Let's analyze a bit the extension descriptor.

!!! warning
    All the attributes of the **extension.json** descriptor are mandatory.


The `audience` attribute is a list of account roles to with the extension is addressed. For fulfillment automation extensions it must always be `["distributor"]`.

The `readme_url` and `changelog_url` are shown in the Connect UI DevOps module as a reference for teams that operates the extension.

## Add a Dockerfile and a docker-compose.yml to run your extension locally

Add the following docker-compose.yml file to your project root folder:


```
$ touch docker-compose.yml
```

Fill docker-compose.yml with the following content:


```yaml
version: '3'

services:
  tshirt_dev:
    container_name: tshirt_dev
    build:
      context: .
    working_dir: /extension
    command: cextrun -d
    volumes: 
      - .:/extension
    env_file:
      - .tshirt_dev.env

  tshirt_bash:
    container_name: tshirt_bash
    build:
      context: .
    working_dir: /extension
    command: /bin/bash
    stdin_open: true
    tty: true
    volumes:
      - .:/extension
    env_file:
      - .tshirt_dev.env

  tshirt_test:
    container_name: tshirt_test
    build:
      context: .
    working_dir: /extension
    command: extension-test
    volumes:
      - .:/extension
    env_file:
      - .tshirt_dev.env
```


and the following Dockerfile:

```
$ touch Dockerfile
```

and fill it with the following:


```dockerfile
FROM cloudblueconnect/connect-extension-runner:{{ runner_version() }}

COPY pyproject.toml /install_temp/.
COPY poetry.* /install_temp/.
WORKDIR /install_temp
RUN poetry update && poetry install --no-root
COPY package*.json /install_temp/.
RUN if [ -f "/install_temp/package.json" ]; then npm install; fi
```

## Add a the `.tshirt_dev.env` file with your environment variables

Create the env file:

```
$ touch .tshirt_dev.env
```

and fill it with:

```
API_KEY="<< replace with a Connect API key >>"
ENVIRONMENT_ID="<< replace with your DevOps environment ID >>"
SERVER_ADDRESS="api.connect.cloudblue.com"
```
