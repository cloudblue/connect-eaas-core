
## Setup UI files

### package.json

Create an initial package.json to handle javascript dependencies in your project root folder:

```
$ touch package.json
```


and add the following content:

``` json hl_lines="16"
{
  "name": "chart-extension",
  "version": "0.1.0",
  "description": "Chart extension",
  "author": "Globex corporation",
  "main": "index.js",
  "directories": {
    "test": "ui/tests"
  },
  "scripts": {
    "build": "webpack",
  },
  
  "license": "Apache Software License 2.0",
  "dependencies": {
    "@cloudblueconnect/connect-ui-toolkit": "^{{ current_major() }}",
    "@fontsource/roboto": "^4.5.8"
  },
  "devDependencies": {
    "@babel/core": "^7.18.0",
    "@babel/preset-env": "^7.18.0",
    "css-loader": "^6.7.1",
    "file-loader": "^6.2.0",
    "html-webpack-plugin": "^5.5.0",
    "mini-css-extract-plugin": "^2.6.1",
    "style-loader": "^3.3.1",
    "webpack": "^5.74.0",
    "webpack-cli": "^4.10.0",
    "copy-webpack-plugin": "^11.0.0",
    "css-minimizer-webpack-plugin": "^4.2.2"
  }
}
```

The `connect-ui-toolkit` module allow your extension UI to communicate with the Connect UI.



### webpack.config.js

To build the final UI artifacts add a [webpack](https://webpack.js.org) configuration file:


```
$ touch webpack.config.js
```

and put the following content:

``` js
const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const CssMinimizerPlugin = require("css-minimizer-webpack-plugin");
const CopyWebpackPlugin = require('copy-webpack-plugin');

const generateHtmlPlugin = (title) => {
  const moduleName = title.toLowerCase();

  return new HtmlWebpackPlugin({
    title,
    filename: `${moduleName}.html`,
    template: `./ui/pages/${moduleName}.html`,
    chunks: [moduleName]
  });
}

const populateHtmlPlugins = (pagesArray) => {
  res = [];
  pagesArray.forEach(page => {
    res.push(generateHtmlPlugin(page));
  })
  return res;
}

const pages = populateHtmlPlugins(["Index", "Settings"]);

module.exports = {
  mode: 'production',
  entry: {
    index: __dirname + "/ui/src/pages/index.js",
    settings: __dirname + "/ui/src/pages/settings.js"
  },
  output: {
    filename: '[name].[contenthash].js',
    path: path.resolve(__dirname, 'e2e/static'),
    clean: true,
  },
  optimization: {
    splitChunks: {
      cacheGroups: {
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          chunks: 'all',
        },
      },
    },
     minimizer: [
      new CssMinimizerPlugin(),
    ],
  },
  plugins: [
    ...pages,
    new CopyWebpackPlugin({
      patterns: [
        { from: __dirname + "/ui/images", to: "images" },
      ],
    }),
    new MiniCssExtractPlugin({
      filename: "index.css",
      chunkFilename: "[id].css",
    }),
  ],
  module: {
    rules: [
      {
        test: /\.css$/i,
        use: [MiniCssExtractPlugin.loader, "css-loader"],
      },
      {
        test: /\.(woff(2)?|ttf|eot|svg)(\?v=\d+\.\d+\.\d+)?$/,
        use: [
          {
            loader: 'file-loader',
            options: {
              name: '[name].[ext]',
              outputPath: 'fonts/'
            },
          },
        ],
      },
    ],
  },
}
```

This configuration will handle two HTML pages, `settings.html` which will be embedded
within the `Account Settings` module of Connect UI and `index.html` that will be the
main page of your extension and will be renderer inside the UI of Connect as a standalone
module.

### babel.config.json

To allow the usage of ECMAScript 6 modules you can use [babel](https://babeljs.io) so a basic
`babel.config.json` is needed:

```
$ touch babel.config.json
```

with following content:

``` json
{
  "presets": ["@babel/preset-env"]
}
```

### Source files directories

Finally you have to create the following folders for storing the UI source files:

```
.
└── <project_root>
    ├── ui
    │   ├── pages
    │   ├── images
    │   ├── src
    │   │   └── pages
    │   └── styles
```

So in your project root execute:

```
$ mkdir -p ui/{pages,images,src/pages,styles}
```

## Add HTML sources

First create the two pages inside the `ui/pages` folder:

```
$ touch ui/pages/{index,settings}.html
```

Then fill the ui/pages/index.html with:

``` html
<!DOCTYPE html>
<html>

<head>
    <meta charset="utf-8" />
    <title>
        <%= htmlWebpackPlugin.options.title %>
    </title>
</head>

<body>
    <div id="loader"></div>
    <div id="app">
        <main-card title="Distribution of active subscriptions per marketplace">
            <div class="main-container">
                <div id="chart">
                </div>
                <div>
                    <div class="list-wrapper">
                        <ul id="marketplaces" class="list">
                        </ul>
                    </div>
                </div>
            </div>
        </main-card>
    </div>
</body>

</html>
```

and ui/pages/settings.html with:

``` html
<!DOCTYPE html>
<html>

<head>
    <meta charset="utf-8" />
    <title>
        <%= htmlWebpackPlugin.options.title %>
    </title>
</head>

<body>
    <div id="loader"></div>
    <div id="app">
        <settings-card title="Choose your marketplaces you want to include in chart">
            <div class="list-wrapper">
                <ul id="marketplaces" class="list">
                </ul>
            </div>
            <div class="button-container">
                <button id="save" class="button" disabled>SAVE</button>
            </div>
        </settings-card>
    </div>
    <div id="error">
        <settings-card title="Error">
            <div class="error-message">
                <p id="error-message">Something went wrong. Please try to reload the page.</p>
            </div>
        </settings-card>
    </div>
</body>

</html>
```

## Add an image to use for missing Marketplace icons

Create the mkp.svg file:

```
$ touch ui/images/mkp.svg
```

and fill it with:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 0 24 24" width="24">
   <path d="M0 0h24v24H0z" fill="none" />
   <path d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zm6.93 6h-2.95c-.32-1.25-.78-2.45-1.38-3.56 1.84.63 3.37 1.91 4.33 3.56zM12 4.04c.83 1.2 1.48 2.53 1.91 3.96h-3.82c.43-1.43 1.08-2.76 1.91-3.96zM4.26 14C4.1 13.36 4 12.69 4 12s.1-1.36.26-2h3.38c-.08.66-.14 1.32-.14 2 0 .68.06 1.34.14 2H4.26zm.82 2h2.95c.32 1.25.78 2.45 1.38 3.56-1.84-.63-3.37-1.9-4.33-3.56zm2.95-8H5.08c.96-1.66 2.49-2.93 4.33-3.56C8.81 5.55 8.35 6.75 8.03 8zM12 19.96c-.83-1.2-1.48-2.53-1.91-3.96h3.82c-.43 1.43-1.08 2.76-1.91 3.96zM14.34 14H9.66c-.09-.66-.16-1.32-.16-2 0-.68.07-1.35.16-2h4.68c.09.65.16 1.32.16 2 0 .68-.07 1.34-.16 2zm.25 5.56c.6-1.11 1.06-2.31 1.38-3.56h2.95c-.96 1.65-2.49 2.93-4.33 3.56zM16.36 14c.08-.66.14-1.32.14-2 0-.68-.06-1.34-.14-2h3.38c.16.64.26 1.31.26 2s-.1 1.36-.26 2h-3.38z" />
</svg>
```


## Add a CSS to style your pages

First create a CSS file in the `styles` directory:

```
$ touch ui/styles/index.css
```

Then fill it with:

``` css
body {
    font-family: "Roboto", sans-serif;
}

.hidden {
    display: none !important;
}

#loader {
    width: 48px;
    height: 48px;
    border: 5px solid white;
    border-bottom-color: #1565c0;
    border-radius: 50%;
    display: block;
    margin: 0 auto;
    box-sizing: border-box;
    animation: rotation 1s linear infinite;
    }

    @keyframes rotation {
    0% {
        transform: rotate(0deg);
    }
    100% {
        transform: rotate(360deg);
    }
}


h1 {
    font-weight: 500;
    font-size: 20px;
}


.switch {
    z-index: 0;
    position: relative;
    display: inline-block;
    color: rgba(var(--pure-material-onsurface-rgb, 0, 0, 0), 0.87);
    font-family: var(--pure-material-font, "Roboto", "Segoe UI", BlinkMacSystemFont, system-ui, -apple-system);
    font-size: 16px;
    line-height: 1.5;
}

/* Input */
.switch>input {
    appearance: none;
    -moz-appearance: none;
    -webkit-appearance: none;
    z-index: -1;
    position: absolute;
    right: 6px;
    top: -8px;
    display: block;
    margin: 0;
    border-radius: 50%;
    width: 40px;
    height: 40px;
    background-color: rgba(var(--pure-material-onsurface-rgb, 0, 0, 0), 0.38);
    outline: none;
    opacity: 0;
    transform: scale(1);
    pointer-events: none;
    transition: opacity 0.3s 0.1s, transform 0.2s 0.1s;
}

/* Span */
.switch>span {
    display: inline-block;
    width: 100%;
    cursor: pointer;
}

/* Track */
.switch>span::before {
    content: "";
    float: right;
    display: inline-block;
    margin: 5px 0 5px 10px;
    border-radius: 7px;
    width: 36px;
    height: 14px;
    background-color: rgba(var(--pure-material-onsurface-rgb, 0, 0, 0), 0.38);
    vertical-align: top;
    transition: background-color 0.2s, opacity 0.2s;
}

/* Thumb */
.switch>span::after {
    content: "";
    position: absolute;
    top: 2px;
    right: 16px;
    border-radius: 50%;
    width: 20px;
    height: 20px;
    background-color: rgb(var(--pure-material-onprimary-rgb, 255, 255, 255));
    box-shadow: 0 3px 1px -2px rgba(0, 0, 0, 0.2), 0 2px 2px 0 rgba(0, 0, 0, 0.14), 0 1px 5px 0 rgba(0, 0, 0, 0.12);
    transition: background-color 0.2s, transform 0.2s;
}

/* Checked */
.switch>input:checked {
    right: -10px;
    background-color: rgb(var(--pure-material-primary-rgb, 33, 150, 243));
}

.switch>input:checked+span::before {
    background-color: rgba(var(--pure-material-primary-rgb, 33, 150, 243), 0.6);
}

.switch>input:checked+span::after {
    background-color: rgb(var(--pure-material-primary-rgb, 33, 150, 243));
    transform: translateX(16px);
}

/* Hover, Focus */
.switch:hover>input {
    opacity: 0.04;
}

.switch>input:focus {
    opacity: 0.12;
}

.switch:hover>input:focus {
    opacity: 0.16;
}

/* Active */
.switch>input:active {
    opacity: 1;
    transform: scale(0);
    transition: transform 0s, opacity 0s;
}

.switch>input:active+span::before {
    background-color: rgba(var(--pure-material-primary-rgb, 33, 150, 243), 0.6);
}

.switch>input:checked:active+span::before {
    background-color: rgba(var(--pure-material-onsurface-rgb, 0, 0, 0), 0.38);
}

/* Disabled */
.switch>input:disabled {
    opacity: 0;
}

.switch>input:disabled+span {
    color: rgb(var(--pure-material-onsurface-rgb, 0, 0, 0));
    opacity: 0.38;
    cursor: default;
}

.switch>input:disabled+span::before {
    background-color: rgba(var(--pure-material-onsurface-rgb, 0, 0, 0), 0.38);
}

.switch>input:checked:disabled+span::before {
    background-color: rgba(var(--pure-material-primary-rgb, 33, 150, 243), 0.6);
}

.button-container {
    display: flex;
    flex-direction: row-reverse;
    align-items: flex-end;
    margin-right: 15px;
}

.button {
    position: relative;
    display: inline-block;
    box-sizing: border-box;
    border: none;
    border-radius: 4px;
    padding: 0 8px;
    min-width: 64px;
    height: 36px;
    vertical-align: middle;
    text-align: center;
    text-overflow: ellipsis;
    text-transform: uppercase;
    color: rgb(var(--pure-material-primary-rgb, 33, 150, 243));
    background-color: transparent;
    font-family: var(--pure-material-font, "Roboto", "Segoe UI", BlinkMacSystemFont, system-ui, -apple-system);
    font-size: 14px;
    font-weight: 500;
    line-height: 36px;
    overflow: hidden;
    outline: none;
    cursor: pointer;
}

.button::-moz-focus-inner {
    border: none;
}

/* Overlay */
.button::before {
    content: "";
    position: absolute;
    left: 0;
    right: 0;
    top: 0;
    bottom: 0;
    background-color: currentColor;
    opacity: 0;
    transition: opacity 0.2s;
}

/* Ripple */
.button::after {
    content: "";
    position: absolute;
    left: 50%;
    top: 50%;
    border-radius: 50%;
    padding: 50%;
    width: 32px;
    height: 32px;
    background-color: currentColor;
    opacity: 0;
    transform: translate(-50%, -50%) scale(1);
    transition: opacity 1s, transform 0.5s;
}

/* Hover, Focus */
.button:hover::before {
    opacity: 0.04;
}

.button:focus::before {
    opacity: 0.12;
}

.button:hover:focus::before {
    opacity: 0.16;
}

/* Active */
.button:active::after {
    opacity: 0.16;
    transform: translate(-50%, -50%) scale(0);
    transition: transform 0s;
}

/* Disabled */
.button:disabled {
    color: rgba(var(--pure-material-onsurface-rgb, 0, 0, 0), 0.38);
    background-color: transparent;
    cursor: initial;
}

.button:disabled::before {
    opacity: 0;
}

.button:disabled::after {
    opacity: 0;
}

.list-wrapper {
    margin: 30px auto;
}

.list {
    background-color: #FFF;
    margin: 0;
    padding: 15px;
    border-radius: 2px;
}

.list .list-item {
    display: flex;
    padding: 10px 5px;
}

.list .list-item .switch {
    display: flex;
    align-items: center;
}

.list .list-item:not(:last-child) {
    border-bottom: 1px solid #EEE;
}

.list .image {
    flex-shrink: 0;
    height: 80px;
}

.list .list-item-image img {
    width: 70px;
    height: 70px;
}

.list .list-item-content {
    width: 90%;
    padding: 0 20px;
}

.list .list-item-content h4 {
    margin: 0;
    font-size: 18px;
    margin-top: 15px;
}

.list .list-item-content p {
    margin-top: 5px;
    color: #AAA;
    margin-bottom: 0;
}

.main-container {
    display: flex;
    flex-direction: row;
    justify-content: space-evenly;
    align-items: center;
}
```

## Add a js module with utility functions

Now add a file called `utils.js`:

```
$ touch ui/src/utils.js
```

with the following content:

``` js
export const getSettings = () => fetch('/api/settings').then((response) => response.json());

export const getChart = () => fetch('/api/chart').then((response) => response.json());

export const getMarketplaces = () => fetch('/api/marketplaces').then((response) => response.json());

export const updateSettings = (settings) => fetch('/api/settings', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(settings),
}).then((response) => response.json());

// data processing
export const processMarketplaces = (
  allMarketplaces,
  selectedMarketplaces,
) => allMarketplaces.map((marketplace) => {
  const checked = !!selectedMarketplaces.find(
    (selectedMarketplace) => selectedMarketplace.id === marketplace.id,
  );

  return { ...marketplace, checked };
});

export const processSelectedMarketplaces = (
  allMarketplaces,
  checkboxes,
) => checkboxes.map((checkbox) => allMarketplaces.find(
  (marketplace) => marketplace.id === checkbox.value,
));

export const processCheckboxes = (
  checkboxes,
) => Array.from(checkboxes).filter(checkbox => checkbox.checked);
```

In this `utils.js` you have functions resposible for API calls as long as for
data processing.

## Add a js module to manipulate UI components


Create a file called `components.js`:

```
$ touch ui/src/components.js
```

with the following content:

``` js
export const prepareMarketplaces = (marketplaces) => {
  try {
    return marketplaces.reduce((list, marketplace) => `${list}<li class="list-item">
        <div class="list-item-image">
          <img src="${marketplace.icon}" alt="Thumbnail">
        </div>
        <div class="list-item-content">
          <h4>${marketplace.id} - ${marketplace.name}</h4>
          <p>${marketplace.description}</p>
        </div>
      </li>`, '');
  } catch (e) { return ''; }
};

export const prepareMarketplacesWithSwitch = (marketplaces) => {
  try {
    return marketplaces.reduce((list, marketplace) => `${list}<li class="list-item">
        <div class="list-item-image">
          <img src="${marketplace.icon}" alt="Thumbnail">
        </div>
        <div class="list-item-content">
          <h4>${marketplace.name}</h4>
          <p>${marketplace.description}</p>
        </div>
        <div class="list-item switch">
          <label class="switch">
              <input type="checkbox" role="switch" value="${marketplace.id}"${marketplace.checked ? ' checked' : ''}>
              <span></span>
          </label>
        </div>
      </li>`, '');
  } catch (e) { return ''; }
};

export const prepareChart = (chartData) => `<img src="https://quickchart.io/chart?c=${encodeURI(JSON.stringify(chartData))}">`;

// render UI components
export const renderMarketplaces = (marketplaces) => {
  const element = document.getElementById('marketplaces');
  element.innerHTML = marketplaces;
};

export const renderChart = (chart) => {
  const element = document.getElementById('chart');
  element.innerHTML = chart;
};

// render UI components - buttons
export const enableButton = (id, text) => {
  const element = document.getElementById(id);
  element.disabled = false;
  if (text) element.innerText = text;
};

export const disableButton = (id, text) => {
  const element = document.getElementById(id);
  element.disabled = true;
  if (text) element.innerText = text;
};

export const addEventListener = (id, event, callback) => {
  const element = document.getElementById(id);
  element.addEventListener(event, callback);
};

// render UI components - show/hide
export const showComponent = (id) => {
  if (!id) return;
  const element = document.getElementById(id);
  element.classList.remove('hidden');
};

export const hideComponent = (id) => {
  if (!id) return;
  const element = document.getElementById(id);
  element.classList.add('hidden');
};
```

## Add the pages.js module

Create a file called `pages.js`:

```
$ touch ui/src/pages.js
```

with the following content:

``` js hl_lines="33 35 68"
import {
  getChart,
  getMarketplaces,
  getSettings,
  processCheckboxes,
  processMarketplaces,
  processSelectedMarketplaces,
  updateSettings,
} from './utils';

import {
  addEventListener,
  disableButton,
  enableButton,
  hideComponent,
  prepareChart,
  prepareMarketplaces,
  prepareMarketplacesWithSwitch,
  renderChart,
  renderMarketplaces,
  showComponent,
} from './components';


export const saveSettingsData = async (app) => {
  if (!app) return;
  disableButton('save', 'Saving...');
  try {
    const allMarketplaces = await getMarketplaces();
    const checkboxes = processCheckboxes(document.getElementsByTagName('input'));
    const marketplaces = processSelectedMarketplaces(allMarketplaces, checkboxes);
    await updateSettings({ marketplaces });
    app.emit('snackbar:message', 'Settings saved');
  } catch (error) {
    app.emit('snackbar:error', error);
  }
  enableButton('save', 'Save');
};

export const index = async () => {
  hideComponent('app');
  showComponent('loader');
  const settings = await getSettings();
  const chartData = await getChart();
  const chart = prepareChart(chartData);
  const marketplaces = prepareMarketplaces(settings.marketplaces);
  hideComponent('loader');
  showComponent('app');
  renderChart(chart);
  renderMarketplaces(marketplaces);
};

export const settings = async (app) => {
  if (!app) return;
  try {
    hideComponent('app');
    hideComponent('error');
    showComponent('loader');
    const allMarketplaces = await getMarketplaces();
    const { marketplaces: selectedMarketpaces } = await getSettings();
    const preparedMarketplaces = processMarketplaces(allMarketplaces, selectedMarketpaces);
    const marketplaces = prepareMarketplacesWithSwitch(preparedMarketplaces);
    renderMarketplaces(marketplaces);
    enableButton('save', 'Save');
    addEventListener('save', 'click', saveSettingsData.bind(null, app));
    showComponent('app');
  } catch (error) {
    app.emit('snackbar:error', error);
    showComponent('error');
  }
  hideComponent('loader');
};
```

In this module can be found the functions `index` and `settings` that implement the application 
logic for the your extension's main module and the `Account Settings` page respectively.

!!! note
    This functions receive an `Connect UI Toolkit` application as the argument.
    Among other functionalities, the `Connect UI Toolkit` allow to send events
    to the Connect UI.
    You can see how your extension emit events to make the Connect UI open
    the snackbar component to notify success and error events to the user.


## Add entrypoint modules for loading inside the HTML pages

Finally add two js modules:

```
$ touch ui/src/pages/{index,settings}.js
```

Then, fill the `index.js` page with the following content:

```js
import createApp, {
  Card,
} from '@cloudblueconnect/connect-ui-toolkit';
import {
  index,
} from '../pages';
import '@fontsource/roboto/500.css';
import '../../styles/index.css';


createApp({ 'main-card': Card })
  .then(() => { index(); });
```


and `settings.js` with the following:

```js
import createApp, {
  Card,
} from '@cloudblueconnect/connect-ui-toolkit';
import {
  settings,
} from '../pages';
import '@fontsource/roboto/500.css';
import '../../styles/index.css';


createApp({ 'settings-card': Card })
  .then(settings);
```

As you can see this two js files act as the entrypoint for index.html and settings.html respectively.

!!! note
    Please also note that in these entrypoint an instance of the `Connect UI Toolkit` application
    is instantiated and then passed to the `index` and `settings` function described above.
    The argument of the `createApp` function is an object that tell to the application to
    export a `Card` widget as an HTML custom element.


## Rebuild your Docker image

As you did for testing your extension's API run:

``` bash
$ docker compose build
```

This time this build installs the Node.js dependencies you declared in your `package.json`.


## Run your extension

``` bash
$ docker compose up chart_dev
```

When the container starts, it will build your UI artifacts.

