import store from "/src/store/local";
import PortfolioCustomization from "/src/models/PortfolioCustomization";
import StockModification from "/src/models/StockModification";
import TargetPortfolioModel from "/src/models/TargetPortfolioModel";
import instance from "/src/api/instance";
import ListModification from "/src/models/ListModification";

function isObjectEmpty(obj) {
  if (!obj) {
    return true;
  }
  return Object.keys(obj).length === 0;
}
const storageAPI = {
  setDefaults(value) {
    const final: Array<any> = [];
    value.forEach((val, key) => {
      const destructured = { ...val };
      destructured.excludedLists = Array.from(destructured.excludedLists);
      destructured.excludedTickers = Array.from(destructured.excludedTickers);
      final.push({ key: key, value: destructured });
    });
    store.set("customizations", final);
  },

  getDefaults() {
    const dat: Array<any> = ((store.get("customizations") as unknown) ||
      []) as Array<any>;
    const final = new Map();
    dat.forEach((item) => {
      if (isObjectEmpty(item.value.excludedLists)) {
        item.value.excludedLists = new Set();
      } else {
        item.value.excludedLists = new Set(item.value.excludedLists);
      }
      if (isObjectEmpty(item.value.excludedTickers)) {
        item.value.excludedTickers = new Set();
      } else {
        item.value.excludedTickers = new Set(item.value.excludedTickers);
      }
      try {
        item.value.stockModifications = item.value.stockModifications.map(
          (item) => new StockModification(item.ticker, item.scale, null),
        );
      } catch (e) {
        item.value.stockModifications = [];
      }
      try {
        item.value.listModifications = item.value.listModifications.map(
          (item) => new ListModification(item.list, item.scale),
        );
      } catch (e) {
        item.value.listModifications = [];
      }
      // item.value.listModifications = item.value.listModifications.map((item) => new ListModification(item.list, item.scale))
      final.set(item.key, new PortfolioCustomization(item.value));
    });
    return final;
  },
};

function customizationDefault(): Map<String, PortfolioCustomization> {
  return new Map();
}

const state = {
  customizations: customizationDefault(),
  stockLists: [],
  targetPortfolios: new Map(),
  // excludedTickers: new Set(),
  // excludedLists: new Set(),
  // stockModifications: [],
  // listModifications: [],
  // stockLists: {} // {list_name: [ticker1, ticker2, ...]}
};

const getters = {
  portfolioCustomizations: (state) => state.customizations,
  // excludedTickers: state => state.excludedTickers,
  // excludedLists: state => state.excludedLists,
  // stockModifications: state => state.stockModifications,
  // listModifications: state => state.listModifications,
  stockLists: (state) => state.stockLists,
  getCustomizationByName: (state) => (name) => {
    return safeGetCustomization(state, name);
  },
  getTargetPortfolioByName: (state) => (name) => {
    return safeGetTargetPortfolio(state, name);
  },
  // totalModifications: state => state.stockModifications.length + state.listModifications.length + state.excludedLists.size + state.excludedTickers.size,
};

// const helpers = {
// };

const actions = {
  async getStockLists({ commit }) {
    await instance.get("stock_lists").then((response) => {
      commit("setStockLists", { stockLists: response.data.loaded });
    });
  },

  async setTargetPortfolio({ commit }, data) {
    commit("setTargetPortfolio", data);
  },

  async setStockLists({ commit }, data) {
    commit("setStockLists", data);
  },
  async setPortfolioTargetIndex({ commit }, data) {
    if (!data.index) {
      return;
    }
    commit("setPortfolioTargetIndex", data);
    commit("saveCustomizations");
  },
  async excludeStock({ commit }, data) {
    commit("excludeStock", data);
    commit("saveCustomizations");
  },
  async removeStockExclusion({ commit }, data) {
    commit("removeStockExclusion", data);
    commit("saveCustomizations");
  },
  async modifyStock({ commit }, data) {
    commit("modifyStock", data);
    commit("saveCustomizations");
  },
  async removeStockModification({ commit }, data) {
    commit("removeStockModification", data);
    commit("saveCustomizations");
  },

  async excludeList({ commit }, data) {
    commit("excludeList", data);
    commit("saveCustomizations");
  },
  async removeListExclusion({ commit }, data) {
    commit("removeListExclusion", data);
    commit("saveCustomizations");
  },

  async modifyList({ commit }, data) {
    commit("modifyList", data);
    commit("saveCustomizations");
  },
  async saveCustomizations({ commit }) {
    commit("saveCustomizations");
    // commit('saveDefaults')
  },
  async loadCustomizations({ commit }) {
    const data = storageAPI.getDefaults();
    commit("commitCustomizations", data);
  },
  async loadDefaultModifications({ commit }) {
    commit("loadDefaults", storageAPI.getDefaults());
  },
  async clearAllModifications({ commit }) {
    commit("clearAllModifications");
  },
};

function safeGetCustomization(state, name: String) {
  if (!name) {
    throw new Error("No name provided for customization");
  }
  const customization = state.customizations.get(name);
  if (customization) {
    return customization;
  }
  const newPortfolio = new PortfolioCustomization({
    reweightIndex: true,
    indexPortfolio: null,
    excludedLists: new Set(),
    excludedTickers: new Set(),
    stockModifications: [],
    listModifications: [],
  });
  state.customizations.set(name, newPortfolio);
  return newPortfolio;
}

function safeGetTargetPortfolio(state, name: String) {
  if (!name) {
    throw new Error("No name provided for getting target");
  }
  const target = state.targetPortfolios.get(name);
  if (target) {
    return target;
  }
  const newPortfolio = new TargetPortfolioModel({
    holdings: [],
    source_date: "2000-01-01",
    name: "placeholder",
  });
  state.targetPortfolios.set(name, newPortfolio);
  return newPortfolio;
}

const mutations = {
  setStockLists(state, data) {
    state.stockLists = data.stockLists;
  },
  excludeStock(state, data) {
    const customization = safeGetCustomization(state, data.portfolioName);
    customization.excludedTickers.add(data.ticker);
  },
  setTargetPortfolio(state, data) {
    state.targetPortfolios.set(data.portfolioName, data.targetPortfolio);
  },
  removeStockExclusion(state, data) {
    const customization = safeGetCustomization(state, data.portfolioName);
    if (data.mode === "exclusion") {
      customization.excludedTickers.delete(data.ticker);
    } else if (data.mode === "modification") {
      customization.stockModifications =
        customization.stockModifications.filter(
          (item) => item.ticker !== data.ticker,
        );
    }
  },
  modifyStock(state, data) {
    safeGetCustomization(state, data.portfolioName).stockModifications.push(
      new StockModification(data.ticker, data.scale, data.minWeight),
    );
  },
  removeStockModification(state, data) {
    const customization = safeGetCustomization(state, data.portfolioName);
    customization.stockModifications = customization.stockModifications.filter(
      (item) => item.ticker !== data.ticker,
    );
  },
  excludeList(state, data) {
    safeGetCustomization(state, data.portfolioName).excludedLists.add(
      data.list,
    );
  },
  removeListExclusion(state, data) {
    safeGetCustomization(state, data.portfolioName).excludedLists.delete(
      data.list,
    );
  },
  modifyList(state, data) {
    // push the entire object here
    const customization = safeGetCustomization(state, data.portfolioName);
    customization.listModifications = customization.listModifications.filter(
      (item) => item.list !== data.list,
    );
    customization.listModifications.push(
      new ListModification(data.list, data.scale),
    );
  },
  removeListModification(state, data) {
    const customization = safeGetCustomization(state, data.portfolioName);
    customization.listModifications = customization.listModifications.filter(
      (item) => item.list !== data.list,
    );
  },
  saveCustomizations(state) {
    storageAPI.setDefaults(state.customizations);
  },
  commitCustomizations(state, data) {
    if (data === undefined) return;
    state.customizations = data;
  },
  // loadDefaults(state, data) {
  //     if (data === undefined) return

  //     state.customizations = data
  // },
  clearAllModifications(state, data) {
    const customization = safeGetCustomization(state, data.portfolioName);
    customization.listModifications = [];
    customization.stockModifications = [];
    customization.excludedLists = new Set();
    customization.excludedTickers = new Set();
  },
  setPortfolioTargetIndex(state, data) {
    const customization = safeGetCustomization(state, data.portfolioName);
    customization.indexPortfolio = data.index;
  },
};

export default {
  state,
  getters,
  actions,
  mutations,
};
