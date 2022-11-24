An extension represents a python package with a predefined structure. 
Depending on the type of the extension, it may also include one or multiple applications. 

In turn, your deployed applications can provide a set of different features depending on your 
selected application type. The following describes application types that can be incorporated 
by your extension:

## Types of applications

### Events Applications

Events applications, as the name implies, are used to work with various events on the CloudBlue 
Connect platform and your external systems. Such applications respond to two types of events:

* status changes of any object on the Connect platform
* trigger activations of a scheduled task

In addition, note that event applications are supported by all extension types.

### Web Applications

Web applications allow extending the functionality of Connect API by adding custom methods and custom endpoints.
Such applications can also be used to establish new modules on Connect UI. Consequently, this allows users of 
your extension to access your defined features via extended API or via the provided graphical user interface.     
  
Note that web applications are supported only by *Multi-Account* and *Hub Integration* extensions.

### Anvil Applications

These applications enable linking the Connect platform with your web interface built 
via [Anvil.Works](https://anvil.works). 

The functionality of such applications is not limited to a specific 
extension type. Therefore, your anvil application can represent your commerce system for hub integrations, 
a fulfillment automation system, or a multi-account extension.


## Supported application types per extension type

In the following table you can see the supported application types given an extension type.

|Extension Type|Events Application|Web Application API|Web Application UI|Anvil Application|
|--------------|:----------------:|:-------------:|:-------------:|:---------------:|
|Fulfillment Automation|:material-check:{ .green }|:material-close:{ .red }|:material-close:{ .red }|:material-check:{ .green }|
|Hub Integration|:material-check:{ .green }|:material-check:{ .green }|:material-close:{ .red }|:material-check:{ .green }|
|Multi Account Installation|:material-check:{ .green }|:material-check:{ .green }|:material-check:{ .green }|:material-check:{ .green }|
