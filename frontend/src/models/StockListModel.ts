export default class StocklistInventoryResponse {
  keys: Set<string>;
  base: string;
  loaded: any;
  
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