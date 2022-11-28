The following describes tools that are available to facilitate and streamline your extension development.

## Connect CLI

The [Connect Command Line Interface](https://github.com/cloudblue/connect-cli) allows bootstrapping an extension project and validating your configured extension.

### Bootstrap an extension project

In order to bootstrap a new extension project, open your terminal and run:

```
$ ccli project extension bootstrap
```

Thereafter, follow the instructions of the project bootstrap wizard.

### Validate an extension project

To validate an extension project, open your terminal and run:

```
$ ccli project extension validate <your project folder>
```

## Connect Python OpenAPI Client

The [Connect Python OpenAPI Client](https://connect-openapi-client.readthedocs.io/en/latest)
is one of the main tools for developing your extension.

This client can be instantiated by using [Connect Extension Runner](https://github.com/cloudblue/connect-extension-runner)
and your generated API key. It is available within your application code as a part of your
application class for `Events` and `Anvil` applications. It is also available within the FastAPI dependency injection framework for
`Web` applications.


## Connect UI Toolkit

The [Connect UI Toolkit](https://github.com/cloudblue/connect-ui-toolkit)
is a javascript library that enable your extension UI to communicate with the Connect UI.
It allows listening to Connect UI events, watching the Connect UI exposed properties, and also adding
basic widgets to your extension UI.

!!! note
    The `Connect UI Toolkit` is under development and thus more widgets will be added soon.  
    So stay tuned!


## Example extensions

There are two `Multi Account Installation` extensions that are provided by the CloudBlue Connect Team. The source code of these extensions is publicly available on github.


### Telegram Notifications

The `Telegram Notifications` extension allows selecting a set of events and users that should receive notifications
via [Telegram](https://telegram.org) groups.


This `Multi Account Installation` extension implements both a `Web Application` and an `Events Application`.
The `Web Application` is embedded in the `Settings` module of the Conenct platform. The provided interface allows configuring the
Telegram group chat id, the Telegram authentication token, and events your users are interested in.


The git repository of this extension is available here: [https://github.com/cloudblue/connect-extension-telegram-notifications](https://github.com/cloudblue/connect-extension-telegram-notifications).


### Activation Notifications

The `Activation Notifications` extension is used to send emails to customers and notify that their subscription has been activated.

It is a bit more complex than `Telegram Notifications` since it uses a PostreSQL database as a service to persist
the extension data.

This `Multi Account Installation` implements both a `Web Application` and an `Events Application`.

The `Web Application` is embedded in the `Settings` module of Conenct. The provided interface allows configuring
per-product email templates that are used to define your notification email body. It also features a standalone module
to access logs of your sent emails.

The `Events Application` reacts to `subscription approved` events and send such notifications to specified addresses.


The git repository of this extension is available here: [https://github.com/cloudblue/connect-extension-service-delivery-notifications](https://github.com/cloudblue/connect-extension-service-delivery-notifications).
