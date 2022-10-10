This tutorial will take you step by step to create a `Hub Integration` extension that implements an anvil application.

!! note
    All the concepts you will learn in this tutorial are also applicable to extension types `Fulfillment Automation` and `Multi Account Installation`.

An anvil application allows you to integrate an Anvil Client Application with CloudBlue Connect like shown in the following diagram:

![Anvil App Diagram](../../images/tutorials/anvilapp/anvil_app_diagram.png)

Following this tutorial you will create an Anvil Client Application that allows you to create a purchase order for a t-shirt.

![Anvil UI](../../images/tutorials/anvilapp/anvil_ui.png)


!!! note
    For more information about Anvil and Anvil Server Uplink visit the [Anvil Website](https://anvil.works) and [Anvil Uplink documentation](https://anvil.works/docs/uplink).


!!! note
    This tutorial assumes that you are using a *nix operating system, if you are on windows you have to convert shell commands to windows.

