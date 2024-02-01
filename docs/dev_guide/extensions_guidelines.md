This article pretends to give some guideles on tech stack, code style and tools that Connect team considers usefull and easiest to get starting with extensions.


## Tech Stack

- ORM and db toolkit: SQLAlchemy
- Database: PostgresSQL
- Web framework: FastAPI 
- Pagination: fastapi-pagination
- Filtering and sorting: fastapi_filter
- Api data representation: pydantic
- Dependency managment: poetry
- Docker for extension execution: Using connect-extension-runner image.

## Testing
	
- PyTest
- Factory boy: pytest-factoryboy
- pytest-asyncio to test code that uses asyncio. 


## Code styling

### [Flake8](https://flake8.pycqa.org/en/latest/)

Next we show the list of all plugins that are included by default on template's project.

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

Another tool that it's not included in our stack yet, but you may want to consider to add on top, it's [black](https://black.readthedocs.io/en/stable/).

If that's the case, you'll need to include the next packages.

* black
* flake8-black

## CI/CD

### Tests workflow 

By default, our bootstrap will create a github workflow with 4 jobs, 3 for backend tests, one per each one of this python versions: 3.8, 3.9, 3.10.
Here, we have to clarify that the only mandatory version at this moment is 3.10, which is the one that its included in the latest connect-extension-runner. The other two can be removed if there is no intention of exposing this extension to be run in your own servers.

The 4th job is the one in charge of running frontend tests.


## Another Tools

[Connect-cli](https://github.com/cloudblue/connect-cli)

[Docker compose](https://docs.docker.com/compose/)

[Poetry](https://python-poetry.org/docs/basic-usage/)
