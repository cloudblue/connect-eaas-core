## Requirements

Make sure that the following prerequisites are met:

* Python (3.8, 3.9 or 3.10) is installed 
* [Docker](https://www.docker.com/) is installed
* The latest release of [Poetry](https://python-poetry.org/) is installed


## Bootstrap a new project

Create a `pyproject.toml` file with general information on your extension project:

```
$ mkdir chart_extension
$ cd chart_extension
$ poetry init --name chart-extension --description "Chart extension" --author "Globex corporation" --python ">=3.8,<3.11" --dependency="connect-eaas-core>={{ core_version() }},<{{ next_major() }}" --no-interaction
```

Use the `poetry init` command to create a `pyproject.toml` file with the following data:

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

Next, create a *root python package* for your project, a *readme* file and a *changelog* file:

```
$ mkdir chart_extension
$ touch README.md
$ touch CHANGELOG.md
```

## Create a descriptor file

Create a descriptor file with essential information on your extension project. Use the following 
command to create an empty JSON file inside your extension root package:

```
$ touch chart_extension/extension.json
```

!!! note
    The name of your descriptor file must always be **extension.json**. It also must be located 
    inside the root package of your extension project.


Next, open your created extension.json file by using your code editor and provide the following data:

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

!!! warning
    All attributes of the **extension.json** descriptor file are mandatory!

The provided example assumes that your extension code will be hosted on **github.com** within the `myaccount` account and your repository is called `chart_extension`.

The `name`, `description` and `version` attributes are used to generate the [OpenAPI](https://www.openapis.org/) specifications for your extension's REST API.

The `audience` attribute represents a list of account roles in Connect. Thus, it is required to specify which roles are supported by your extension. In case your extension is published, Connect allows filtering out and locating your extension by using your specified  roles on the platform.

The `readme_url` and `changelog_url` will be presented in the Connect UI DevOps module as a reference for teams that will work with your extension. The `changelog_url` attribute will be used as *Version History* details for your extension once it is published in the Showroom Catalog.

The `icon` attribute allows you to customize the material design icon of your extension for the Connect UI dashboard page.

!!! note
    It is required to use icons from the Connect Material Icons package. Use one of the provided folder names as your icon attribute. See the list of all available icons by using this link:
    [https://github.com/cloudblue/material-svg/tree/main/icons/google](https://github.com/cloudblue/material-svg/tree/main/icons/google).


## Dockerfile and `docker-compose.yml` 

Create a `dockerfile` and a `docker-compose.yml` and to run your extension locally. First, add a new *docker-compose.yml* file to your project root folder:


```
$ touch docker-compose.yml
```

Populate your `docker-compose.yml` with necessary data as follows:


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


Next, create an empty dockerfile by using the following command:


```
$ touch Dockerfile
```

Add the following code to your dockerfile:


```dockerfile
FROM cloudblueconnect/connect-extension-runner:{{ runner_version }}

COPY pyproject.toml /install_temp/.
COPY poetry.* /install_temp/.
WORKDIR /install_temp
RUN poetry update && poetry install --no-root
COPY package*.json /install_temp/.
RUN if [ -f "/install_temp/package.json" ]; then npm install; fi
```

## Create `.chart_dev.env`

Make sure to add a new `env file` with your environment variables:

```
$ touch .chart_dev.env
```

Enter the following variables within your created env file:

```
API_KEY="<< replace with a Connect API key >>"
ENVIRONMENT_ID="<< replace with your DevOps environment ID >>"
SERVER_ADDRESS="api.connect.cloudblue.com"
```
