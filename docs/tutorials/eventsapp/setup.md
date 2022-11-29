## Requirements

Make sure that the following prerequisites are met:

* Python (3.8, 3.9 or 3.10) is installed 
* [Docker](https://www.docker.com/) is installed
* The latest release of [Poetry](https://python-poetry.org/) is installed


## Bootstrap a new project

Start working with your extension by creating a `pyproject.toml` file with general information on your extension project:


```
$ mkdir chart_extension
$ cd chart_extension
$ poetry init --name tshirt-extension --description "T-Shirt extension" --author "Globex corporation" --python ">=3.8,<3.11" --dependency="connect-eaas-core>={{ core_version() }},<{{ next_major() }}" --no-interaction
```

Use the `poetry init` command to create a `pyproject.toml` file with the following data:

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

Next, create a *root python package* for your project, a *readme* file and a *changelog* file:

```
$ mkdir tshirt_extension
$ touch README.md
$ touch CHANGELOG.md
```

## Add a descriptor file

Create a descriptor file with essential information on your extension project. Use the following 
command to create an empty JSON file inside your extension root package: 

```
$ touch tshirt_extension/extension.json
```

!!! note
    The name of your descriptor file must always be **extension.json**. It also must be located 
    inside the root package of your extension project.


Next, open your created extension.json file by using your favorite code editor and provide the following data:

```
{
    "name": "tshirt",
    "description": "This extension automates fulfillment processing for a t-shirt product.",
    "version": "1.0.0",
    "audience": ["vendor"],
    "readme_url": "https://raw.githubusercontent.com/myaccount/tshirt_extension/master/README.md",
    "changelog_url": "https://raw.githubusercontent.com/myaccount/tshirt_extension/master/CHANGELOG.md"
}
```
!!! warning
    All attributes of the **extension.json** descriptor file are mandatory!

The provided example assumes that your extension code will be hosted on **github.com** within the `myaccount` account and that your repository is called `tshirt_extension`.

The `audience` attribute represents a list of account roles in Connect. Thus, it is required to specify which roles are supported by your extension. For instance, fulfillment automation extensions should include `["vendor"]` within this attribute.

The `readme_url` and `changelog_url` attributes will be presented in the Connect UI DevOps module as a reference for teams that will work with your extension.

## Dockerfile and `docker-compose.yml` 

Create a `dockerfile` and a `docker-compose.yml` and to run your extension locally. First, add a new *docker-compose.yml* file to your project root folder:


```
$ touch docker-compose.yml
```

Populate your `docker-compose.yml` with necessary data as follows:


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


Next, create an empty dockerfile by using the following command:

```
$ touch Dockerfile
```

Add the following code to your dockerfile:


```dockerfile
FROM cloudblueconnect/connect-extension-runner:{{ runner_version() }}

COPY pyproject.toml /install_temp/.
COPY poetry.* /install_temp/.
WORKDIR /install_temp
RUN poetry update && poetry install --no-root
COPY package*.json /install_temp/.
RUN if [ -f "/install_temp/package.json" ]; then npm install; fi
```

## Create `.tshirt_dev.env`

Make sure to add a new `env file` with your environment variables:

```
$ touch .tshirt_dev.env
```

Enter the following variables within your created env file:

```
API_KEY="<< replace with a Connect API key >>"
ENVIRONMENT_ID="<< replace with your DevOps environment ID >>"
SERVER_ADDRESS="api.connect.cloudblue.com"
```
