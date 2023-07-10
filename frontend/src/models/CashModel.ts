export default class CashModel {
    currency:string;
    value: number;

    constructor({currency, value}) {
        this.currency = currency;
        this.value = value;
    }
} 