This tutorial will take you step by step to create a `Multi Account Installation` extension that implements a web application.
This web application plugs into CloudBlue Connect user interface adding a module that render a bar chart that shows the distribution of active assets per marketplace.

![Chart module](../../images/tutorials/webapp/chart_module.png)

It will also add a settings page to the `Account Settings` module that will allow account users to select the marketplaces for which the user want to draw the diagram from the list of marketplaces visible by the account that install this extension.

![Chart settings](../../images/tutorials/webapp/chart_settings.png)

In the first part of the tutorial you will create the REST API that your user interface will consume.
In the second part you will create the user interface for your web application.

The backend of a web application is based on the Python web framework [FastAPI](https://fastapi.tiangolo.com/), but you can easly complete the tutorial even if you are not familiar with such web framework.


!!! note
    This tutorial assumes that you are using a *nix operating system, if you are on windows you have to convert shell commands to windows.

