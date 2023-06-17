export default class TargetPortfolioElement {
  ticker: string;
  weight: string;
    constructor({ticker, weight}) {
      this.ticker = ticker;
      this.weight = weight;
    }
  }
  