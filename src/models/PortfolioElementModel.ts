
class PortfolioElementValueModel {
  value:string;
  currency:string;
  constructor({value, currency}) {
    this.value = value
    this.currency = currency
  }
}

export default class PortfolioElementModel {
  ticker:string;
  unit:string;
  value:PortfolioElementValueModel;
  weight:string;
  
  constructor({ticker, unit, value, weight}) {
    this.ticker = ticker
    this.unit=unit
    this.value = new PortfolioElementValueModel(value)
    this.weight=weight
  }
} 