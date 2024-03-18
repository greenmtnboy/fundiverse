# Installation

### Open Source Platform

Fundiverse is an Electron desktop app with versions for Windows, Mac, and Linux. You download and run it like any other program on your computer. 

::: tip
Electron is a common packaging format for distributing apps. It is used by many popular tools such as Slack, Discord, and Visual Studio Code.
:::

### Python Backend

The app is built on top of a python backend that does the heavy lifting of talking to brokerages and placing orders. The python backend is also open source and can be installed and run independently of the Electron app.

::: tip
Tech savvy? UIs not your thing? Install the python backend directly [here](https://github.com/greenmtnboy/py-portfolio-index) and build your own tools on top.
:::

### Data Stays Private

You install Fundiverse, and then locally configure it to connect to your brokerage (such as Robinhood, Alpaca, or others) by providing it with API keys. Your computer talks directly to the brokerages - Fundiverse will not send data to anything other than the brokerages you have configured. 

### Bring your Own Brokerage

Fundiverse will use your brokerage to determine what stocks you hold, their current prices, and other market information and then determine
what orders to place to help build your customized index. You can then have it place those orders for you given rules you define.

### Get Started Quickly

A portfolio will be set up with a target size and can either be fully funded or built towards over time. A portfolio can be revisited to be rebalanced or to add more funds.

::: tip
Your portfolio can even span multiple brokerages!
:::
