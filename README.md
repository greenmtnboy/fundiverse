
## Fundiverse is Stock Accumulation Platform

Indexing has been a gospel of long-term investing for years. The central tenet of buying diverse funds that capture large portions of the market and holding them for a long-duration has proven it's value again and again.

However, the emergence of low and no-fee trading platforms has made a previously prohibitive option easy - building your own index. 

Fundiverse is a platform to enable you to have fun diversifying your index. Take the gold standard as a model, and add your personal touch to it. Exclude coal stocks? Sure. All in on solar? Why not weight those 400%. Hate fruit? Mark Apple down 50%.

![UI Preview](https://github.com/greenmtnboy/fundiverse/blob/main/media/ui-example.png)

## What is it not?
Fundiverse is not an effective tool for day trading or short-term holding in general.

## Installation
Currently only supported on Windows. Open an issue for Linux or Mac. 

Download the latest release .exe from [the releases page](https://github.com/greenmtnboy/fundiverse/releases), or click for [direct download](https://github.com/greenmtnboy/fundiverse/releases/download/v0.1.2/fundiverse-Setup-0.1.2.exe).

Run the downloaded exe to install, then start it as a standard application. You'll have to accept the unsafe publisher + potentially allow firewall access. Fundiverse needs to communicate with itself and with your brokerage provider. 

## Why would you do this?
Besides just being more fun than being an index, customization can enable you to weigh specific factors that are either morally important to you - such as not investing in oil companies - or that you believe will outperform the market - such as investing in companies with a high ESG score or in a sector you think will outperform.

Fundiverse also makes it easy to exclude companies you can't trade in, such as your employer or companies you have a conflict of interest with. 

## How does it work?

Fundiverse is built on an [open-source python framework](https://github.com/greenmtnboy/py-portfolio-index) for building ideal and real portfolios and purchasing large amounts of stocks against various backends to bring the real portfolio in line with the ideal. Fundiverse wraps this in an Electron desktop app, which simplifies the process of creating curated indices and understanding how your changes adjust the composition of the stocks. 

## Supported Platforms
Fundiverse requires you to have an account sent up with one of the following platforms.

- Alpaca
- Robinhood [WIP]
- TD Ameritrade [WIP]

## Trying it out
We recommend you start out with an Alpaca paper trading account, which will let you experiment without exposing any real money to the platform. You can log into your production account at any point to try out ideas for real. 


