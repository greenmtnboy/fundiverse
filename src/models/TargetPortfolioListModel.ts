

export default class TargetPortfolioListModel {
  loaded: any;
  constructor({loaded}) {
    // this.keys = new Set(keys);
    // this.base = base;
    this.loaded = loaded || {};
  }

  // static fromApiResponse(response) {
  //   const { keys, base, loaded } = response;
  //   return new IndexInventoryResponse(keys, base, loaded);
  // }
}

