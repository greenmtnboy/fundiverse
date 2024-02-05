
export default class StockModification {
    ticker: string
    scale?: number
    minWeight?: number

    constructor(ticker, scale, minWeight) {
        this.ticker = ticker
        this.scale = scale
        this.minWeight = minWeight
    }
} 