This article pretends to give some guidelines on the tech stack, code style and tools that the Connect team considers useful and easiest to get started with extensions.


## Tech Stack

- ORM and db toolkit: SQLAlchemy
- Database: PostgresSQL
- Web framework: FastAPI 
- Pagination: fastapi-pagination
- Filtering and sorting: fastapi_filter
- Api data representation: pydantic
- Dependency management: poetry
- Docker for extension execution: Using connect-extension-runner image.
- Frontend framework: Vue 3

## Testing
	
- PyTest
- Factory boy: pytest-factoryboy
- pytest-asyncio to test code that uses asyncio. 


## Code styling

### [Flake8](https://flake8.pycqa.org/en/latest/)

Next, we show the list of all plugins that are included by default in the template's project.

 * max-lines: 100
 * max-cognitive-complexity: 15
 * import-order-style = smarkets
 * flake8-bugbear
 * flake8-commas
 * flake8-future-import
 * flake8-import-order
 * flake8-broken-line
 * flake8-comprehensions
 * flake8-debugger
 * flake8-eradicate
 * flake8-string-format

Another tool that's not included in our stack yet, but you may want to consider adding it on top, is [black](https://black.readthedocs.io/en/stable/).

If that's the case, you'll need to include the following packages.

* black
* flake8-black

## Frontend

### Development
In the Connect team, we use [Vue 3](https://vuejs.org/) to develop the frontend for our extensions, but this is not binding; any framework (or even vanilla JS) can be used. Vue 3 is not included in the extensions bootstrapped via the Connect CLI.

We also use the [Connect UI Toolkit](https://github.com/cloudblue/connect-ui-toolkit) library to deal with the communication from the extensions to the Connect Portal, such as requesting data, sending events or performing navigation from within the extensions. This library also exposes multiple web components, styled like the Connect Portal components, that can be used in the extensions, such as icons, cards, or navigation components, among others, and other useful tools, and it is included by default in the extensions bootstrapped via the Connect CLI.

### Builds
It is very important to note that **the static distribution files need to be in version control**, since there is no build process when running the extensions in cloud mode. Make sure you commit your distribution files!

### Tooling
An extension bootstrapped via the Connect CLI will come with several tools already configured:
- [Webpack](https://webpack.js.org/), to build and bundle the frontend codebase
- [Jest](https://jestjs.io/), to run unit tests
- [ESLint](https://eslint.org/), to lint the code

You can use any other tool as a replacement, as these libraries are only used for development. You might consider using [Vite](https://vitejs.dev/) and [Vitest](https://vitest.dev/) instead of Webpack and Jest, or add [Prettier](https://prettier.io/) to format the code; we use these tools in some of our extensions.


## CI/CD

### Tests workflow 

By default, our bootstrap will create a GitHub workflow with 4 jobs, 3 for backend tests, and one for each of these python versions: 3.8, 3.9, 3.10.
Here, we have to clarify that the only mandatory version at this moment is 3.10, which is the one that's included in the latest `connect-extension-runner`. The other two can be removed if there is no intention of exposing this extension to be run on your own servers.

The fourth job is the one in charge of running frontend tests.


## Other Tools

[Connect-cli](https://github.com/cloudblue/connect-cli)

[Docker compose](https://docs.docker.com/compose/)

[Poetry](https://python-poetry.org/docs/basic-usage/)
