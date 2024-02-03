export default class TargetPortfolioModification {
  modification_type: string;
  tickers: Array<string>;

  constructor({ modification_type, tickers }) {
    this.modification_type = modification_type;
    this.tickers = tickers;
  }
}
