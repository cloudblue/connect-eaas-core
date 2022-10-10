Now that your `Anvil Application` is ready it's time to test it.

To do that you need:

* A CloudBlue Connect **vendor** account
* A CloudBlue Connect **distributor** account
* An Anvil trial account


## Create a t-shirt product

!!! note
    If you are not familiar with the `Products` module of Connect you can read the documentation in the Connect
    [community portal](https://connect.cloudblue.com/community/modules/products/).

* As a `vendor` go to the Connect User Interface and create a t-shirt product.
* In the `General` view edit the short description for your t-shirt product.
* In the `General` view edit the `overview` text for your product.
* In the `General` view select the `Media` tab and add a primary image for your tshirt.
* Go to the `Parameters` view and remove the parameters that have been created by default.
* Add a product `ordering` parameter with a `subscription` scope of type `choice`.
* Add the following choices:
    *   label `XS` value `xs`
    *   label `S` value `s`
    *   label `M` value `m`
    *   label `L` value `l`
    *   label `XL` value `xl`
* Set the parameter ID to `size`.
* Go to the `Versions` view and create a public version of your t-shirt product.

!!! tip
    Please record the product id since you will need it later in this article.

## Create a Listing Request to list your product in your distributor account

!!! note
    If you are not familiar with the `Listings` module of Connect you can read the documentation in the Connect
    [community portal](https://connect.cloudblue.com/community/modules/listings/).

* As the `vendor` go to the `Listings` module and click the button `Manage Listing`.
* Follow the `Manage Listing` wizard and select a Marketplace and your distributor account.

!!! tip
    Please record the marketplace id since you will need it later in this article.


## List the t-shirt product

* As the `distributor` go to the `Listings` module and in the `Requests` tab click on
the request for your t-shirt product.
* Click on the button `Mark as deploying` than on the button `Mark as completed`

## Connect the t-shirt product with your hub

!!! note
    If you are not familiar on how to create a product to hub connection read the article on our
    [community portal](https://connect.cloudblue.com/community/modules/marketplaces/connections/).

* As the `distributor` go to the `Products` module and open your t-shirt product.
* In the `Connections` view create a new `Connection`.

!!! tip
    Please record the connection id since you will need it later in this article.


## Create the Anvil Client Application

Once you have created your [Anvil](https://anvil.works) trial account you have to create your Anvil Client Application.
To do that quickly you can [download a pre-created application from this link](../../assets/anvil_application_tutorial.yml).

Go to your Anvil account and from the main menu in the header bar choose `My Apps`
Once on the `My Apps` page click on the link `Import from file`:

![Import Anvil Client App](../../images/tutorials/anvilapp/anvil_import_from_file.png)

Once loaded the file, the Anvil editor will be shown. In the left side bar click on the :material-cog: icon and choose `Uplink...`:

![Setup Anvil 1](../../images/tutorials/anvilapp/anvil_setup_uplink_1.png)

In the `Anvil Uplink` dialog click on the button `Enable the Anvil Server Uplink for this app`:

![Setup Anvil 2](../../images/tutorials/anvilapp/anvil_setup_uplink_2.png)

Once pressed the `Uplink key` will be shown.

!!! tip
    Please record the uplink key since you will need it later in this article.


Close the `Anvil Uplink` dialog and in the `Main Form` editor click on the `Code` button.

Fill the `PRODUCT_ID` constant with the id of your t-shirt product.


## Create a `Hub Integration` extension

To do that you first need to go to the Connect UI to create an extension of type `Hub Integration`.
As the `distributor` from the main menu, navigate to the `DevOps` module and click the `Add extension` button
Fill the Add extension form like in the following picture choosing the product you created in the previous step:

![Add extension](../../images/tutorials/anvilapp/add_extension.png)

Once created, open the details view of your brand new extension:

![List extensions](../../images/tutorials/anvilapp/list_extensions.png)

And select the `DEV` environment tab:

![Extension details](../../images/tutorials/anvilapp/extension_details.png)

Go to the `Local Access` widget and click on the :material-content-copy: button to copy your environment ID.


## Update your `.tshirt_dev.env` environment file 

Edit your `.tshirt_dev.env` file and fill the `ENVIRONMENT_ID` variable with the copied value.


!!! warning
    This tutorial assume that you know how to create a Connect API key and that the
    `API_KEY` variable of the `.tshirt_dev.env` file is set with a valid value.
    For more information about how to create an API Key visit the
    [Connect Community Portal](https://connect.cloudblue.com/community/modules/extensions/api-tokens/).


## Build a Docker image for your extension

To build the Docker image for your extension run:


``` bash
$ docker compose build
```

## Run your extension

Once the image is build, to run your container execute:

``` bash
$ docker compose up tshirt_dev
```

Now go to the Connect UI and check that your extension is connected to the `DEV` environment
using the :material-refresh: button located in the `Environment` widget.

In the `Environment Variables` widget set the right value for each variable with the value
your recorded during this tutorial, then click the `Apply changes` button.


## Create a purchase request from your Anvil Client Application

Go to the Anvil application editor and click the `Run` button placed in the header bar.

Once your application is loaded, choose a size for the t-shirt from `size` the dropdown menu,
enter an integer value for the `quantity` then press the `Buy Now` button.

!!! success "Congratulations"
    :partying_face: your first `Anvil Application` works like a charm :beers:
