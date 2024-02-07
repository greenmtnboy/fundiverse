import StockModification from "./StockModification";
import ListModification from "./ListModification";

function assertIsSet(value) {
  if (!(value instanceof Set)) {
    throw new Error("Expected a Set.");
  }
}

export default class PortfolioCustomization {
  indexPortfolio: string;
  reweightIndex: boolean;
  excludedTickers: Set<String>;
  excludedLists: Set<String>;
  stockModifications: Array<StockModification>;
  listModifications: Array<ListModification>;

  constructor({
    indexPortfolio,
    reweightIndex,
    excludedTickers,
    excludedLists,
    stockModifications,
    listModifications,
  }) {
    assertIsSet(excludedTickers);
    assertIsSet(excludedLists);
    this.indexPortfolio = indexPortfolio;
    this.reweightIndex = reweightIndex;
    this.excludedTickers = excludedTickers;
    this.excludedLists = excludedLists;
    this.stockModifications = stockModifications;
    this.listModifications = listModifications;
  }

  get customizationCount() {
    return (
      this.stockModifications.length +
      this.listModifications.length +
      this.excludedLists.size +
      this.excludedTickers.size
    );
  }
}
