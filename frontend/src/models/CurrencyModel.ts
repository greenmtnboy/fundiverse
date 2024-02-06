export default class CurrencyModel {
  value: string;
  currency: string;
  constructor({ value, currency }) {
    this.value = value;
    this.currency = currency;
  }
}
