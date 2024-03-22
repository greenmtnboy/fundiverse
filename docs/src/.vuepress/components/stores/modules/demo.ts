import TargetPortfolioModel from "../../models/TargetPortfolioModel";
import PortfolioCustomization from "../../models/PortfolioCustomization";
import ListModification from "../../models/ListModification";
import StockModification from "../../models/StockModification";
import TargetPortfolioElementModel from "../../models/TargetPortfolioElementModel";
import CompositePortfolioModel from "../../models/CompositePortfolioModel";
import CashModel from "../../models/CashModel";
import PortfolioModel from "../../models/PortfolioModel";
import PortfolioElementModel from "../../models/PortfolioElementModel";
import SubPortfolioModel from "../../models/SubPortfolioModel";


const StaticWeights= {
  'AAPL': {'actual': 20000, 'goal': 20000},
  'MSFT': {'actual': 17000, 'goal': 17000},
  'AMZN': {'actual': 13000, 'goal': 13000},
  'TSLA': {'actual': 10000, 'goal': 10000},
  'META': {'actual': 10000, 'goal': 10000},
  'BRK.B': {'actual': 10000, 'goal': 10000},
  'JPM': {'actual': 5000, 'goal': 5000},
  'JNJ': {'actual': 5000, 'goal': 5000},
  'RKLB': {'actual': 1007, 'goal': 0},
  'HD': {'actual': 0, 'goal': 5000},
}

const totalGoal = 100000;
const totalActual = [...Object.values(StaticWeights)].map(x => x.actual).reduce((partialSum, a) => partialSum + a, 0);

const storageAPI = {
  getPortfolio(): TargetPortfolioModel {
    let port = new TargetPortfolioModel({
      holdings: [],
      source_date: "2023-01-01",
      name: "test",
    });
    return port;
  },
  // Create a static target
  getStaticDemoTargetPortfolio(): TargetPortfolioModel {
    let targetHoldings = [...Object.entries(StaticWeights)].map((values) => {
      let ticker = values[0]
      let weight = values[1];
      let goal = weight.goal;
      if (!goal) {
        return null;
      }
      return new TargetPortfolioElementModel({ ticker:ticker, weight:goal/totalGoal});
    })
    let port = new TargetPortfolioModel({
      holdings: targetHoldings.filter(x => x !== null),
      source_date: "2023-01-01",
      name: "example_target",
    });
    return port;
  },
  // Create a static actual
  getStaticDemoPortfolio(): CompositePortfolioModel {
    let holdings = [...Object.entries(StaticWeights)].map((values) => {
      let ticker = values[0]
      let weight = values[1];
      return new PortfolioElementModel({
        ticker: ticker,
        weight: weight.actual / totalActual /100,
        value: { value: weight.actual + Math.random()*500 -250, currency: "USD" },
        targetWeight: weight.goal/totalGoal,
        dividends : { value: Math.random()*100, currency: "USD" },
        appreciation : { value: Math.random()*1000, currency: "USD" },
      });
    })
    let port = new SubPortfolioModel({
      holdings:holdings,
      source_date: "2023-01-01",
      name: "test",
      profit_and_loss: { value: 1100, currency: "USD" },
      cash: { value: 10, currency: "USD" },
    })
    let profit = holdings.map(x => x.appreciation.value + x.dividends.value).reduce((partialSum, a) => partialSum + a, 0);
    let composite = new CompositePortfolioModel({
      holdings: port.holdings,
      source_date: "2023-01-01",
      name: "My Portfolio",
      components: [port],
      profit_and_loss: { value: profit, currency: "USD" },
      cash: { value: 10, currency: "USD" },
      target_size: 100_000,
      refreshed_at: 1711118442
    });
    return composite;
  },
  getCustomization(target) {
    return new PortfolioCustomization({
      reweightIndex: true,
      indexPortfolio: target,
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
  staticDemoPortfolio: storageAPI.getStaticDemoPortfolio(),
  staticDemoTargetPortfolio: storageAPI.getStaticDemoTargetPortfolio(),
  portfolioTarget: 100_000,
  stockLists: {},
  indexes: [storageAPI.getStaticDemoTargetPortfolio()],
  customization: storageAPI.getCustomization(),
  staticCustomization: storageAPI.getCustomization('example_target'),
  python: null,
};

const getters = {
  demoPortfolio: (state) => state.demoPortfolio,
  staticDemoPortfolio: (state) => state.staticDemoPortfolio,
  staticDemoTargetPortfolio: (state) => state.staticDemoTargetPortfolio,
  portfolioTarget: (state) => state.portfolioTarget,
  stockLists: (state) => state.stockLists,
  indexes: (state) => state.indexes,
  portfolioCustomization: (state) => state.customization,
  staticCustomization: (state) => state.staticCustomization,
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
    if (!python) {
      return {'name': data, 'exchange': 'If connected to a brokerage, this would give you information on the exchange.'}
    }
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
      getters.portfolioCustomization
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
          (item) => item.ticker !== data.ticker
        );
    }
  },
  modifyStock(state, data) {
    const customization = state.customization;
    customization.stockModifications.push(
      new StockModification(data.ticker, data.scale, data.minWeight)
    );
  },
  removeStockModification(state, data) {
    const customization = state.customization;
    customization.stockModifications = customization.stockModifications.filter(
      (item) => item.ticker !== data.ticker
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
      (item) => item.list !== data.list
    );
    customization.listModifications.push(
      new ListModification(data.list, data.scale)
    );
  },
  removeListModification(state, data) {
    const customization = state.customization;
    customization.listModifications = customization.listModifications.filter(
      (item) => item.list !== data.list
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
