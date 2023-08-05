
export default class StockModification {
    ticker: string
    weight?: number

    constructor(ticker, weight) {
        this.ticker = ticker
        this.weight = weight
    }
} 