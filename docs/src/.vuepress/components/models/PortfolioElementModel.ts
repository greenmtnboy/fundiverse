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
    targetWeight,
  }) {
    this.ticker = ticker;
    this.unit = unit;
    this.value = new CurrencyModel(value);
    this.weight = weight;
    this.unsettled = unsettled;
    this.targetWeight = targetWeight;
    if (dividends) {
      this.dividends = new CurrencyModel(dividends);
    } else {
      this.dividends = null;
    }
    if (appreciation) {
      this.appreciation = new CurrencyModel(appreciation);
    } else {
      this.appreciation = null;
    }
  }
}
