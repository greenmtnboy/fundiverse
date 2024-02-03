export default class TargetPortfolioElement {
  ticker: string;
  weight: number;
  constructor({ ticker, weight }) {
    this.ticker = ticker;
    this.weight = weight;
  }
}
