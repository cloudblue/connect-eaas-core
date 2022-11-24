The easiest way to start an extension project is using the CloudBlue [Connect CLI](https://github.com/cloudblue/connect-cli).

To bootstrap the project open a terminal and run:

```
$ ccli project extension bootstrap
```

This command runs a wizard that will guide you through the creation of an extension project:

![Boostrap project](../images/cli/bootstrap_project.png)


Once the wizard is finished the following directory structure will be created:

```
.
└── <project_root>
    ├── <package_name>
    │   ├── __init__.py
    │   ├── extension.json
    │   └── ...
    ├── tests
    │   ├── __init__.py
    │   ├── conftest.py
    │   └── ...
    ├── .git
    ├── .gitignore
    ├── LICENSE
    ├── README.md
    ├── CHANGELOG.md
    ├── HOWTO.md
    ├── docker-compose.yml
    ├── Dockerfile
    ├── .<project_slug>_dev.env
    ├── poetry.toml
    ├── pyproject.toml
    └── ...
```

## Project root content

In the project root folder you will find the following files:

* **README.md:** this readme file is intended to provide a description of your extension project. It is
    used by the pyproject.toml to add a description to your python package and will also be renderered on
    the main page of your git repository in many git hosting services.
* **CHANGELOG.md:** this changelog file is intended to track changes between versions of your extension.
    For `Multi Account Installation` extensions it will be also rendered as part of the information of your extension
    in the CloudBlue Connect Extension Catalog.
* **HOWTO.md:** This file provide some useful information about basic tasks related to the development of your extension.
* **LICENSE:** This file provide the agreement text of the Open Source licence under which you decide to release your extension.
* **poetry.toml:** This file just disable the creation of a Python virtual environment when using Poetry. The creation of a
    virtual environment is disable by default since the development of the extension will be done inside e docker container.
* **.gitignore:** A default .gitignore file is provided to avoid commiting file that should not be commited within the git
    repository like `pyc` files, `coverage.xml` and so on.
* **.&lt;project_slug&gt;_dev.env:** Environment variables file needed to run the extension inside the Docker container. 

The `Connect CLI` will also initialize a git repository for your extension project since to run it in cloud mode it must be
hosted on a git server accesible through internet, therefore the presence of a `.git` directory.


### pyproject.toml

In the root folder of your extension project you will find the pyproject.toml file. This will be used by 
[Poetry](https://python-poetry.org/) to build a package of your extension.


In this file you have to specify both runtime and development dependencies for your extension as long as the entrypoint
for each type of application your extension implements.

!!! note
    The `Connect CLI` extension project bootstrap wizard will fill this file with the only required runtime dependency, i.e. `connect-eaas-core` and some suggested development dependencies for testing and linting your code.

Moreover it will also add the required entrypoints for the applications you choosed to implement during the wizard.

!!! info
    Entrypoints must be declared in the section ```[tool.poetry.plugins."connect.eaas.ext"]``` in the form:
    
        "application_type" = "path.to.package:ApplicationClass"

    <u>An application type can only have **one** entrypoint class</u>.
    
    Available application types are **eventsapp**, **webapp** and **anvilapp**.


### docker-compose.yml

Developing your extension using [Docker](https://docker.com) is not mandatory **but it is strongly recommended**.

The `Connect CLI` will generate a default **docker-compose.yml** and **Dockerfile** for you.

The **docker-compose.yml** defines three services named with your extension name plus the following suffixes:

* **_dev:** it runs your extension locally.
* **_bash:** it allows you to enter the extension container in bash for development and testing purposes.
* **_test:** it runs the linter and the unit tests suite.

### Dockerfile

The **Dockerfile** allows you to build an image with all your python (and optionally node.js) dependencies installed.
It starts from the `Connect Extension Runner` image that is based on the [python 3.10 slim](https://hub.docker.com/_/python)
image. It also includes a node.js runtime version 16.*.


## Python package

The python package will contain the **extension.json** descriptor file plus your application entrypoints:

* **anvil.py:** this file will be present if you choosed to implements an `Anvil Application` in your extension and will contain the anvil application entrypoint class.
* **events.py:** this file will be present if you choosed to implements an `Events Application` in your extension and will contain the events application entrypoint class with an event handler for each event you selected during the wizard. It will also contain an example handler
for scheduled execution.
* **webapp.py:** this file will be present if you choosed to implements an `Web Application` in your extension and will contain the web application entrypoint class.

!!! info
    The name of the entrypoint modules is not mandatory but they should be placed all within the same directory that contains the
    **extension.json** file.


## tests package

The `Connect CLI` assume that you will write unit tests for your extension using [pytest](https://docs.pytest.org/en/7.2.x/).
For this reason you will find this **tests** package and a default [**conftest.py**](https://docs.pytest.org/en/6.2.x/fixture.html)
with some pytest fixures that are useful to test your extension code.

Depending on the application types you selected during the wizard the following files will be present:

* **test_anvil.py:** it will contain examples on how to test your `Anvil Application`.
* **test_events.py:** it will contain examples on how to test your `Events Application`.
* **test_webapp.py:** it will contain examples on how to test your `Web Application`.


## Web Application with UI

If you choosed to create a `Web Application` that embeds in the Connect UI, the following additional files and directories will be
created:

```
.
└── <project_root>
    ├── ui
    │   ├── pages
    │   │   ├── index.html
    │   │   └── settings.html
    │   ├── images
    │   │   └── mkp.svg
    │   ├── src
    │   │   ├── components.js
    │   │   ├── pages
    │   │   │   ├── index.js
    │   │   │   └── settings.js
    │   │   ├── pages.js
    │   │   └── utils.js
    │   ├── styles
    │   │   └── index.css
    │   └── tests
    │       ├── components.spec.js
    │       ├── pages.spec.js
    │       └── utils.spec.js
    ├── __mocks__
    │   ├── fileMock.js
    │   └── styleMock.js
    ├── babel.config.json
    ├── jest.config.js
    ├── webpack.config.js
    └── package.json
```

!!! info
    UI artifacts will be generated within the `static` folder inside your extension python package.


!!! note
    The `Connect CLI` will generate an example UI based written with vanilla javascript.
    You can use Vue.js, Angular, React or any web framework you like. The `Connect UI Toolkit` is a
    framework agnostic library, it can be used with the framework of your choice.


!!! warning
    UI generated artifacts must be places in a folder named `static` and this folder must be placed
    in the same folder where your `Web Application` entrypoint module is located.
    For cloud execution of your extension the content of the `static` folder must be commited
    within the git repository since in cloud mode your UI artifacts are copied to a blob storage and
    served from there.

### package.json

This file contains the configuration needed to handle your UI development using node/npm.
It declare both runtime and development dependencies as long as the following scripts (they can be called using `npm run <script_name>`):

* **build:** it runs **webpack** to produce UI artifacts.
* **watch:** watch for changes to your UI source files and rebuild them if some of them change.
* **lint:** it runs the linter to analyze your code.
* **test:** it runs your tests suite using **jest**.

The `Connect CLI` will add as runtime dependencies the [Connect UI Toolkit](https://github.com/cloudblue/connect-ui-toolkit) library and
the `roboto` fonts.

### webpack.config.js

This file will contain a default [webpack](https://webpack.js.org/) configuration to build your UI artifacts. By default `css` and `js` files will be minifed.
It will also inject the right scripts and css dependencies in your html files.

### babel.config.json

This file will contain a default configuration for [babel](https://babeljs.io/) to allow the usage of ECMAScript 6 modules.

### jest.config.js

This file will contain a default configuration for [Jest](https://jestjs.io/) testing framework.

### ui

The ui folder will contain your UI source files as long as your tests specs.
