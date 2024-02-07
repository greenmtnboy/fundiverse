import TargetPortfolioModel from "../../models/TargetPortfolioModel";
import PortfolioCustomization from "../../models/PortfolioCustomization";
import ListModification from "../../models/ListModification";
import StockModification from "../../models/StockModification";

const storageAPI = {
  getPortfolio(): TargetPortfolioModel {
    let port = new TargetPortfolioModel({
      holdings: [],
      source_date: "2023-01-01",
      name: "test",
    });
    return port;
  },
  getCustomization() {
    return new PortfolioCustomization({
      reweightIndex: true,
      indexPortfolio: null,
      excludedLists: new Set(),
      excludedTickers: new Set(),
      stockModifications: [],
      listModifications: [],
    });
  },
};

async function updatePortfolio(python, customization: PortfolioCustomization) {
  python.globals.set("customization", customization);
  await python.runPythonAsync(`
from copy import deepcopy
from py_portfolio_index import INDEXES
import js
ideal_port = deepcopy(INDEXES[customization.indexPortfolio])

for mutation in customization.stockModifications:
    if mutation.scale:
        ideal_port.reweight([mutation.ticker], weight=mutation.scale, min_weight=0.001)
    else:
        ideal_port.reweight([mutation.ticker], weight=0.0, min_weight=mutation.minWeight)
for list_mutation in customization.listModifications:
    ideal_port.reweight(
        STOCK_LISTS[list_mutation.list],
        weight=list_mutation.scale,
        min_weight=0.001,
    )
ideal_port.exclude(customization.excludedTickers)
for item in customization.excludedLists:
    ideal_port.exclude(STOCK_LISTS[item])
IDEAL_PORT = ideal_port.json()
    `);
  let data = python.globals.get("IDEAL_PORT"); //.toJS({proxies:false})
  let final = JSON.parse(data);
  final.name = customization.indexPortfolio;
  let output = new TargetPortfolioModel(final);
  return output;
}

const state = {
  demoPortfolio: storageAPI.getPortfolio(),
  portfolioTarget: 100_000,
  stockLists: {},
  indexes: {},
  customization: storageAPI.getCustomization(),
  python: null,
};

const getters = {
  demoPortfolio: (state) => state.demoPortfolio,
  portfolioTarget: (state) => state.portfolioTarget,
  stockLists: (state) => state.stockLists,
  indexes: (state) => state.indexes,
  portfolioCustomization: (state) => state.customization,
  stockListsLoading: (state) => state.stockLists.size === 0,
  indexesLoading: (state) => state.indexes.size === 0,
  pythonLoading: (state) => state.python == null,
  python: (state) => state.python,
};

const actions = {
  async getPython({ commit, getters }, data) {
    if (getters.python) {
      return;
    }
    // @ts-ignore
    let pyodide = await loadPyodide();
    // hardcoded as pyiodide had repeated issues loading this
    await pyodide.loadPackage("micropip");
    const micropip = pyodide.pyimport("micropip");
    await micropip.install("py-portfolio-index>=0.0.38");
    commit("getPython", pyodide);
  },
  async setPortfolioSize({ commit }, data) {
    commit("setPortfolioSize", data);
  },
  async getStockInfo({ commit, getters }, data) {
    let python = getters.python;
    python.globals.set("ticker", data);
    let _ = await python.runPythonAsync(`
from py_portfolio_index.common import (
    get_basic_stock_info,
)
basic = get_basic_stock_info(ticker, fail_on_missing=False)
if basic:
    raw_data = basic.json()
else:
    raw_data = '{}'

        `);
    let resp = python.globals.get("raw_data"); //.toJS({proxies:false})
    return JSON.parse(resp);
  },
  async getIndexes({ commit, getters }) {
    let python = getters.python;
    let _ = await python.runPythonAsync(`
from py_portfolio_index import INDEXES
_ = [INDEXES[x] for x in INDEXES.keys]
INDEX_DUMP = INDEXES.json()
`);
    let data = python.globals.get("INDEX_DUMP"); //.toJS({proxies:false})
    commit("setIndexes", JSON.parse(data).loaded);
  },
  async getStockLists({ commit, getters }) {
    let python = getters.python;
    let _ = await python.runPythonAsync(`
from py_portfolio_index import STOCK_LISTS
_ = [STOCK_LISTS[x] for x in STOCK_LISTS.keys]
STOCK_LIST_DUMP = STOCK_LISTS.json()
`);
    let data = python.globals.get("STOCK_LIST_DUMP"); //.toJS({proxies:false})
    commit("setStockLists", JSON.parse(data).loaded);
  },
  async setPortfolioTargetIndex({ commit, dispatch }, data) {
    if (!data.index) {
      return;
    }
    commit("setPortfolioTargetIndex", data);
    commit("saveCustomizations");
    dispatch("refreshPortfolio");
  },
  async refreshPortfolio({ commit, getters }) {
    let newPort = await updatePortfolio(
      getters.python,
      getters.portfolioCustomization,
    );
    commit("refreshPortfolio", newPort);
  },
  async excludeStock({ commit, dispatch }, data) {
    commit("excludeStock", data);
    commit("saveCustomizations");
    dispatch("refreshPortfolio");
  },
  async removeStockExclusion({ commit, dispatch }, data) {
    commit("removeStockExclusion", data);
    commit("saveCustomizations");
    dispatch("refreshPortfolio");
  },
  async modifyStock({ commit, dispatch }, data) {
    commit("modifyStock", data);
    commit("saveCustomizations");
    dispatch("refreshPortfolio");
  },
  async removeStockModification({ commit, dispatch }, data) {
    commit("removeStockModification", data);
    commit("saveCustomizations");
    dispatch("refreshPortfolio");
  },

  async excludeList({ commit, dispatch }, data) {
    commit("excludeList", data);
    commit("saveCustomizations");
    dispatch("refreshPortfolio");
  },
  async removeListExclusion({ commit, dispatch }, data) {
    commit("removeListExclusion", data);
    commit("saveCustomizations");
    dispatch("refreshPortfolio");
  },

  async modifyList({ commit, dispatch }, data) {
    commit("modifyList", data);
    commit("saveCustomizations");
    dispatch("refreshPortfolio");
  },
  async saveCustomizations({ commit }) {
    commit("saveCustomizations");
  },
  // async loadCustomizations({ commit }) {
  //     const data = storageAPI.getDefaults()
  //     commit('commitCustomizations', data)
  // },
  // async loadDefaultModifications({ commit }) {
  //     commit('loadDefaults', storageAPI.getDefaults())
  // },
  async clearAllModifications({ commit }) {
    commit("clearAllModifications");
  },
};

const mutations = {
  async getPython(state, data) {
    state.python = data;
  },
  setPortfolioSize(state, data) {
    state.portfolioTarget = data.size;
  },
  setIndexes(state, data) {
    state.indexes = data;
  },
  setStockLists(state, data) {
    state.stockLists = data;
  },
  saveCustomizations(state) {
    //no-op for now
  },
  excludeStock(state, data) {
    const customization = state.customization;
    customization.excludedTickers.add(data.ticker);
  },
  removeStockExclusion(state, data) {
    const customization = state.customization;
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
    const customization = state.customization;
    customization.stockModifications.push(
      new StockModification(data.ticker, data.scale, data.minWeight),
    );
  },
  removeStockModification(state, data) {
    const customization = state.customization;
    customization.stockModifications = customization.stockModifications.filter(
      (item) => item.ticker !== data.ticker,
    );
  },
  excludeList(state, data) {
    const customization = state.customization;
    customization.excludedLists.add(data.list);
  },
  removeListExclusion(state, data) {
    const customization = state.customization;
    customization.excludedLists.delete(data.list);
  },
  modifyList(state, data) {
    // push the entire object here
    const customization = state.customization;
    customization.listModifications = customization.listModifications.filter(
      (item) => item.list !== data.list,
    );
    customization.listModifications.push(
      new ListModification(data.list, data.scale),
    );
  },
  removeListModification(state, data) {
    const customization = state.customization;
    customization.listModifications = customization.listModifications.filter(
      (item) => item.list !== data.list,
    );
  },
  // loadDefaults(state, data) {
  //     if (data === undefined) return

  //     state.customizations = data
  // },
  clearAllModifications(state, data) {
    const customization = state.customization;
    customization.listModifications = [];
    customization.stockModifications = [];
    customization.excludedLists = new Set();
    customization.excludedTickers = new Set();
  },
  setPortfolioTargetIndex(state, data) {
    state.customization.indexPortfolio = data.index;
  },
  refreshPortfolio(state, data) {
    state.demoPortfolio = data;
  },
};

export const exports = {
  state,
  getters,
  actions,
  mutations,
};
