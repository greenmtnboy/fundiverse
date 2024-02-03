export default class StockModification {
  ticker: string;
  scale?: number;

  constructor(ticker, scale) {
    this.ticker = ticker;
    this.scale = scale;
  }
}
