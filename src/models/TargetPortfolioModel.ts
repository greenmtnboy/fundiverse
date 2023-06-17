

export default class TargetPortfolio {
  holdings:string;
  source_date:string;
  
    constructor({holdings, source_date}) {
      this.holdings = holdings;
      this.source_date = source_date;
    }
  }