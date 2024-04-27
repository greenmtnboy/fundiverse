export default class CurrencyModel {
  value: number;
  currency: string;
  constructor({ value, currency }) {
    this.value = value;
    this.currency = currency;
  }
}
