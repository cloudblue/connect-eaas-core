This tutorial will take you step by step to create a `Fulfillment Automation` extension that implements an events application.

!! note
    All the concepts you will learn in this tutorial are also applicable to extension types `Hub Integration` and `Multi Account Installation`.

!! warning
    The purchase request draft validation is only available for `Fulfillment Automation` extensions.


You will automate the fulfillment of a t-shirt approving the purchase request automatically using the default approval template.
You will also implement the purchase request draft validation to check if the choosed size of the t-shirt is in stock or not.

You will create a schedule that once a day invoke a method of your events application to update the stock status with the size that is out of stock.


!!! note
    This tutorial assumes that you are using a *nix operating system, if you are on windows you have to convert shell commands to windows.

