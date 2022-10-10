## Requirements

To complete this tutorial you need:

* Python 3.8, 3.9 or 3.10
* [Docker](https://www.docker.com/)
* Latest release of [Poetry](https://python-poetry.org/)


## Bootstrap project

Let's start creating a pyproject.toml file with the base information about your extension project:


```
$ mkdir chart_extension
$ cd chart_extension
$ poetry init --name chart-extension --description "Chart extension" --author "Globex corporation" --python ">=3.8,<3.11" --dependency="connect-eaas-core>={{ core_version() }},<{{ next_major() }}" --no-interaction
```

The `poetry init` command will create the following pyproject.toml file:

```
[tool.poetry]
name = "chart-extension"
version = "0.1.0"
description = "Chart extension"
authors = ["Globex corporation"]
readme = "README.md"
packages = [{include = "chart_extension"}]

[tool.poetry.dependencies]
python = ">=3.8,<3.11"
connect-eaas-core = ">={{ core_version() }},<{{ next_major() }}"


[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

Now let's create the root python package of your project, a readme file and a changelog file:

```
$ mkdir chart_extension
$ touch README.md
$ touch CHANGELOG.md
```

## Create the extension project descriptor file

First of all creates an empty descriptor file inside your extension root package:

```
$ touch chart_extension/extension.json
```

!!! note
    The name of the descriptor file must be **extension.json** and must be located inside the root package of your extension project.


Assuming that your extension code will be hosted on **github.com** under the account `myaccount` and the repository name `chart_extension`, open the extension.json file using your favorite editor and fill it with:

```
{
    "name": "Chart",
    "description": "This extension add a new module to CloudBlue Connect UI that renders a bar chart showing the distribution of active assets per marketplace.",
    "version": "1.0.0",
    "audience": ["distributor", "vendor", "reseller"],
    "readme_url": "https://raw.githubusercontent.com/myaccount/chart_extension/master/README.md",
    "changelog_url": "https://raw.githubusercontent.com/myaccount/chart_extension/master/CHANGELOG.md",
    "icon": "bar_chart"
}
```

Let's analyze a bit the extension descriptor.

!!! warning
    All the attributes of the **extension.json** descriptor are mandatory.


The `name`, `description` and `version` attributes are used to generate the [OpenAPI](https://www.openapis.org/) specifications file for your extension's REST API.

The `audience` attribute is a list of account roles to with the extension is addressed. For published extensions, it is used by Connect to filter the extension catalog for a given acount accordingly.

The `readme_url` and `changelog_url` are shown in the Connect UI DevOps module as a reference for teams that operates the extension.
The `changelog_url` is also used to fill the Version History pane of the details of an extension within the public catalog.

The `icon` attribute allows you to customize the material design icon of your extension for the Connect UI dashboard page.

!!! note
    The available icons are the one from the connect material icons package. You can see the list of all available icons here:
    [https://github.com/cloudblue/material-svg/tree/main/icons/google](https://github.com/cloudblue/material-svg/tree/main/icons/google).
    The icon name is the name of the folder that contains the icon.


## Add a Dockerfile and a docker-compose.yml to run your extension locally

Add the following docker-compose.yml file to your project root folder:


```
$ touch docker-compose.yml
```

Fill docker-compose.yml with the following content:


```yaml
version: '3'

services:
  chart_dev:
    container_name: chart_dev
    build:
      context: .
    working_dir: /extension
    command: cextrun -d
    volumes: 
      - .:/extension
    env_file:
      - .chart_dev.env

  chart_bash:
    container_name: chart_bash
    build:
      context: .
    working_dir: /extension
    command: /bin/bash
    stdin_open: true
    tty: true
    volumes:
      - .:/extension
    env_file:
      - .chart_dev.env

  chart_test:
    container_name: chart_test
    build:
      context: .
    working_dir: /extension
    command: extension-test
    volumes:
      - .:/extension
    env_file:
      - .chart_dev.env
```


and the following Dockerfile:

```
$ touch Dockerfile
```

and fill it with the following:


```dockerfile
FROM cloudblueconnect/connect-extension-runner:{{ runner_version }}

COPY pyproject.toml /install_temp/.
COPY poetry.* /install_temp/.
WORKDIR /install_temp
RUN poetry update && poetry install --no-root
COPY package*.json /install_temp/.
RUN if [ -f "/install_temp/package.json" ]; then npm install; fi
```

## Add a the `.chart_dev.env` file with your environment variables

Create the env file:

```
$ touch .chart_dev.env
```

and fill it with:

```
API_KEY="<< replace with a Connect API key >>"
ENVIRONMENT_ID="<< replace with your DevOps environment ID >>"
SERVER_ADDRESS="api.connect.cloudblue.com"
```
