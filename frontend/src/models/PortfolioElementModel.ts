import CurrencyModel from "./CurrencyModel";

export default class PortfolioElementModel {
  ticker: string;
  unit: string;
  value: CurrencyModel;
  weight: number;
  unsettled: boolean;
  targetWeight: number | null;

  constructor({ ticker, unit, value, weight, unsettled }) {
    this.ticker = ticker;
    this.unit = unit;
    this.value = new CurrencyModel(value);
    this.weight = weight;
    this.unsettled = unsettled;
    this.targetWeight = null;
  }
}
