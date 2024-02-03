## Basic Usage

Click ‘add portfolio’ to create and name your first portfolio.

<br>

Groups of stocks that you are purchasing are called `portfolios`. A single brokerage
can only be attached to a single portfolio, but a portfolio can contain multiple brokerages.

<br>

A common pattern is having a `paper` and `real` portfolio; the paper portfolio lets you experiment
while the real contains your actual investments.

<br>

Now you need to connect to a brokerage that lets you buy and hold stocks.

<br/>

Alpaca is an easy one to get started with, so we'll use that for this demo

## Alpaca Setup

Go to [https://alpaca.markets/](https://alpaca.markets/)

<br>

Sign up. You don’t need to connect any bank account info to get a paper account. If you get far enough in the flow for it to prompt you about that, just use the sidebar to click out.

<br>

A paper account lets you trade using fake money. It's a good way to get comfortable with an app or trading platform before committing real funds. Ensure that you see 'paper' in your account info on top right.

<br>

Generate an API key in sidebar on right, save it.

<br>

Go back to your portfolio. Click add provider. Select ‘alpaca paper’ as the type, add in your key and secret. Optionally check ‘save login info’ to persist this for next time you open the app.

<br>

Your portfolio view should now look something like this.

<br>

![alt text](/portfolio-view.png "Portfolio View")

## Create and Customize Index

Now that you’re connected to your brokerage, click ‘configure’ to set the index you want to use. For example, you could pick the sp500 or large cap stocks. You can also customize this index by adding/removing/reweighting particular stocks or lists of stocks.

## Index Customization Screen

The customization screen will show your current holdings on left, and your target holdings on right. Use the dropdown to select a new target index.

<br>

You should also set a taret size. Your weighting within the portfolio will be based on the target size of your portfolio. For example, if you want a portfolio of 10000 dollars, and Apple is 10% of the target index, fundiverse will try to get you 1000 dollars of Apple stock.

<br>

::: tip
You can start out your portfolio with only a portion of your total goal! If you want to get a million dollar portfolio, you can set that and incrementally build towards it over time.
:::

<br>

Click the custom button to adjust this index further, such as by excluding some stocks or overweighting or underweighting certain lists.

![alt text](/fundiverse_new.png "Portfolio Customization Screen")

## Placing Orders

Now it's time to make your portfolio a reality.

<br>

Click the 'buy' button to plan out your orders - this may take some time. You can either have the app attempt to get the stocks with the largest difference from their ultimate target price first, or spread out the amount of money you have over many stocks.

<br>

Fundiverse will find the current prices of the stocks to buy and then place orders with your brokerage; there may be some variance in the price the order is filled at.

<br>

::: warning
Spreading out across all stocks for very large indexes - like the total market - may result in an extremely large number of orders, which will increase the variability of your purchases.
:::

Once the process is done, you'll have a list of planned orders, and where they will be placed.

<br>

![alt text](/submit-order.png "Placing an order")

<br>

Click submit to place the orders. You'll be returned a list of which were placed successfully or not.

<br>

That's it! You now own your stocks!
