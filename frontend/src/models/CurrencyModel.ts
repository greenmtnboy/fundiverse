export default class CurrencyModel {
  value: string;
  currency: string;
  constructor({ value, currency }) {
    this.value = value;
    this.currency = currency;
  }

  add(other) {
    if (other.currency != this.currency) {
      throw new Error("Can only add values with same currency!");
    }
    return new CurrencyModel({
      value: this.value + other.value,
      currency: this.currency,
    });
  }
}
