This tutorial provides step-by-step instructions for creating a `Fulfillment Automation` extension that implements an events application.

!!! note
    Provided concepts from this tutorial are also applicable to the `Hub Integration` and `Multi Account Installation` extensions configuration. Note, however, that the draft purchase request validation is only available for `Fulfillment Automation` extensions.


Use this tutorial to automate your fulfillment processing operations. This tutorial showcases a t-shirt product and its associated purchase request that is approvded automatically using the default subscription approval template.
This tutorial also showcases how to implement the draft purchase requests validation to check whether the selected t-shirt size is in the stock.

Furthermore, this tutorial demonstrates how to create a schedule for your events applicaiton. Specifically, this schedule invokes a method to update your stock status with all sizes that are out of stock once a day.

!!! warning
    This tutorial assumes that you are using a *nix operating system. In case of using Windows, it is required to convert all provided commands to Windows Shell commands.
