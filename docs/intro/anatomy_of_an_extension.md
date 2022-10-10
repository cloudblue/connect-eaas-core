## What is an extension

An extension is a python package with a predefined structure.

Depending on the type of the extension, it may contain one or more application inside it.

## Types of applications

### Events Application

An Events Application is an application that reacts to two types of events:

* the status changes of the objects managed by the Connect platform
* the triggering of a scheduled task

This type of application is supported by any of the types of extensions.

### Web Application

A Web Application in an application that allow to both extend the API of Connect with
custom API endpoints and the Connect User Interface creating custom modules.

Such type of application is only supported by Multi Account extensions.

### Anvil Application

TBD


## Supported application types per extension type

In the following table you can see the supported application types given an extension type.

|Extension Type|Events Application|Web Application|Anvil Application|
|--------------|:----------------:|:-------------:|:---------------:|
|Fulfillment Automation|:material-check:{ .green }|:material-close:{ .red }|:material-check:{ .green }|
|Hub Integration|:material-check:{ .green }|:material-close:{ .red }|:material-check:{ .green }|
|Multi Account Installation|:material-check:{ .green }|:material-check:{ .green }|:material-check:{ .green }|
