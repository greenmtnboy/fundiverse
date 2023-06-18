
import CurrencyModel from './CurrencyModel'

export default class PortfolioElementModel {
  ticker:string;
  unit:string;
  value:CurrencyModel;
  weight:string;

  constructor({ticker, unit, value, weight}) {
    this.ticker = ticker
    this.unit=unit
    this.value = new CurrencyModel(value)
    this.weight=weight
  }
} 