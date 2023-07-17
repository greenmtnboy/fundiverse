export default class PortfolioCustomization {
    indexPortfolio:string
    excludedTickers: Set<String>
    excludedLists: Set<String>
    stockModifications: Array<String>
    listModifications: Array<String>

    constructor({ indexPortfolio, excludedTickers, excludedLists, stockModifications, listModifications }) {
        this.indexPortfolio = indexPortfolio;
        this.excludedTickers = excludedTickers;
        this.excludedLists = excludedLists;
        this.stockModifications = stockModifications;
        this.listModifications = listModifications;
    }

    get getCustomizationCount() {
        return this.stockModifications.length + this.listModifications.length + this.excludedLists.size + this.excludedTickers.size
      }
} 