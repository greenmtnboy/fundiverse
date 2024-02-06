import TargetPortfolioElementModel from "./TargetPortfolioElementModel";


export default class TargetPortfolio {

  holdings: Array<TargetPortfolioElementModel>;
  source_date: string;
  name: string | null;

  constructor({ holdings, source_date, name}) {
    this.holdings = holdings;
    this.source_date = source_date;
    this.name = name
  }

  contains({ticker}) {
    return this.holdings.some(item=> item.ticker == ticker)
  }
}