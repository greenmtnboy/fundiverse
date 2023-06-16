
class PortfolioElementValueModel {
  constructor({value, currency}) {
    this.value = value
    this.currency = currency
  }
}

export default class PortfolioElementModel {
  constructor({ticker, unit, value, weight}) {
    this.ticker = ticker
    this.unit=unit
    this.value = new PortfolioElementValueModel(value)
    this.weight=weight
  }
} 