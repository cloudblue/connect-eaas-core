Some tools are available to help you to develop your extension.

## Connect CLI

The [Connect Command Line Interface](https://github.com/cloudblue/connect-cli) allow you to bootstrap an extension project as long as validating it.

### Bootstrap an extension project

To bootstrap a new extension project open a terminal and run:

```
$ ccli project extension bootstrap
```

and follow the project bootstrap wizard.

### Validate an extension project

To validate an extension project open a terminal and run:

```
$ ccli project extension validate <your project folder>
```

## Connect Python OpenAPI Client

The [Connect Python OpenAPI Client](https://connect-openapi-client.readthedocs.io/en/latest)
is one of the base building blocks to develop and extension.

It will be instantiated by the [Connect Extension Runner](https://github.com/cloudblue/connect-extension-runner)
with the right API key in any moment and will be available in your application code as a member of your
application class for Events and Anvil applications or through the FastAPI dependency injection framework for
Web applications.


## Connect UI Toolkit

The [Connect UI Toolkit](https://github.com/cloudblue/connect-ui-toolkit)
is a javascript library that allow your extension UI to communicate with the Connect UI.
It allows to listen to Connect UI events, watch the Connect UI exposed properties and also provide
some basic widget to use in your extension UI.

!!! note
    The `Connect UI Toolkit` is under heavy development and many more widgets will be added soon.
    Stay tunes!


## Example extensions

There are two `Multi Account Installation` extensions written by the CloudBlue Connect Team whose code is publicly 
available on github.


### Telegram Notifications

The `Telegram Notifications` extension allows to select a set of events about which a user want to receive notifications
in a [Telegram](https://telegram.org) group.


This `Multi Account Installation` implements both a `Web Application` and an `Events Application`.
The `Web Application` embed a UI within the `Account Settings` module of Conenct that allows to configure the
Telegram group chat id, the Telegram authentication token and the events the user is interested in.


The git repository of this extension is available [here](https://github.com/cloudblue/connect-extension-telegram-notifications).


### Activation Notifications

The `Activation Notifications` extension sends email to the customer to notify that her/his subscription has been activated.

It is a bit more complex then the `Telegram Notifications` one since it uses a Postresql database as a service to persist
the extension data.

This `Multi Account Installation` implements both a `Web Application` and an `Events Application`.

The `Web Application` embed a UI within the `Account Settings` module of Conenct that allows to configure
per-product email templates that are used to generate the notification email body. It also embed a module
to allow to access the log of sent emails.

The `Events Application` reacts to the subscription approved event to send such notifications.


The git repository of this extension is available [here](https://github.com/cloudblue/connect-extension-service-delivery-notifications).

