<h1 align="center">Fundiverse</h1>
<p align="center">
Customize your index funds
</p>

![Logo](https://github.com/greenmtnboy/fundiverse/blob/main/media/logo-png.png)

[Website](https://fundiverse.dev/) | [Get Started](https://fundiverse.dev/install/) 

## Fundiverse lets you own the market - your way

- Money never leaves your brokerage
- Customize to your priorities, knowledge, or ethics
- Index the SP500 with as little as $500 dollars

Indexing has been a gospel of long-term investing for years. The central tenet of buying diverse funds that capture large portions of the market and holding them for a long-duration has proven it's value again and again.

However, the emergence of low and no-fee trading platforms has made a previously prohibitive option easy - building your own index. 

Fundiverse is a platform to enable you to have fun diversifying your index. Take the gold standard as a model, and add your personal touch to it. Exclude coal stocks? Sure. All in on solar? Why not weight those 400%. Hate fruit? Mark Apple down 50%.

![UI Preview](https://github.com/greenmtnboy/fundiverse/blob/main/media/fundiverse_new.png)

## What is it not?
Fundiverse is not an effective tool for day trading or short-term holding in general.

## Installation

[Read the docs](https://fundiverse.dev/install/) for detailed instructions. 

### Windows

Download the latest release .exe from [the releases page](https://github.com/greenmtnboy/fundiverse/releases).

Run the downloaded exe to install, then start it as a standard application. You'll have to accept the unsafe publisher + potentially allow firewall access. Fundiverse needs to communicate with itself and with your brokerage provider. 

### Linux

Fundiverse is distributed through the snap store on linux. 

Run `snap install fundiverse` to install the app, then `fundiverse` to start it.

## Why would you do this?
Besides just being more fun than buying an index, customization can enable you to weigh specific factors that are either important to you (morally or financially) - such as not investing in oil companies, or overweighting companies oil companies, or just buying everything but Tesla. 

Fundiverse also makes it easy to exclude companies you can't trade in, such as your employer or companies you have a conflict of interest with. 

## How does it work?

Fundiverse is built on an [open-source python framework](https://github.com/greenmtnboy/py-portfolio-index) for constructing customized portfolios tracking indexes across hundreds of stocks. Fundiverse wraps this in an Electron desktop app, which simplifies the process of creating curated indices and understanding how your changes adjust the composition of the stocks. 

## Supported Platforms
Fundiverse requires you to have an account sent up with one of the following platforms. Alpaca and
Webull both support paper trading to experiment without connecting a real bank account.

- Alpaca
- Robinhood
- Webull

## Getting Started

[Read the docs](https://fundiverse.dev/install/).

