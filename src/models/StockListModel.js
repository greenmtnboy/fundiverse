export default class StocklistInventoryResponse {
    constructor(keys, base, loaded) {
      this.keys = new Set(keys);
      this.base = base;
      this.loaded = loaded || {};
    }
  
    static fromApiResponse(response) {
      const { keys, base, loaded } = response;
      return new StocklistInventoryResponse(keys, base, loaded);
    }
  }