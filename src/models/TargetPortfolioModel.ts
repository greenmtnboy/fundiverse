import TargetPortfolioElementModel from "./TargetPortfolioElementModel";


export default class TargetPortfolio {
  holdings:Array<TargetPortfolioElementModel>;
  source_date:string;
  
    constructor({holdings, source_date}) {
      this.holdings = holdings;
      this.source_date = source_date;
    }
  }