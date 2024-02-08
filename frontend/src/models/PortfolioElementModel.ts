import CurrencyModel from "./CurrencyModel";

export default class PortfolioElementModel {
  ticker: string;
  unit: string;
  value: CurrencyModel;
  weight: number;
  unsettled: boolean;
  targetWeight: number | null;
  dividends: CurrencyModel | null;
  appreciation: CurrencyModel | null;

  constructor({
    ticker,
    unit,
    value,
    weight,
    unsettled,
    dividends,
    appreciation,
  }) {
    this.ticker = ticker;
    this.unit = unit;
    this.value = new CurrencyModel(value);
    this.weight = weight;
    this.unsettled = unsettled;
    this.targetWeight = null;
    this.dividends = new CurrencyModel(dividends);
    this.appreciation = new CurrencyModel(appreciation);
  }

  profit() {
    var defCurrency = new CurrencyModel({ value: 0.0, currency: "USD" });
    return (this.dividends || defCurrency).add(
      this.appreciation || defCurrency,
    );
  }
}
