import Store from "electron-store";
import CompositePortfolioModel from "/src/models/CompositePortfolioModel";
import instance from "/src/api/instance";
import SubPortfolioModel from "/src/models/SubPortfolioModel";
import PortfolioCustomization from "/src/models/PortfolioCustomization";

const storeKey = "compositePortfolios";

const store = new Store<Record<string, Object>>({
  name: "portfolios",
  watch: true,
});

const storageAPI = {
  setPortfolios(value: Array<CompositePortfolioModel>) {
    // const buffer = safeStorage.encryptString(value);
    store.set(storeKey, value);
    // store.set(key, buffer.toString(encoding));
  },

  getPortfolios(): Array<Object> {
    const data = store.get(storeKey, []) as Array<any>;
    const parsed = data.map((dict) => new CompositePortfolioModel(dict));
    return parsed;
  },
};

function defaults() {
  const data: Array<CompositePortfolioModel> = [];
  return data;
}

function mappings() {
  const data: Map<String, PortfolioCustomization> = new Map();
  return data;
}

const state = {
  displayLength: 50,
  compositePortfolios: defaults(),
  portfolioLoadingStatus: false,
  compositePortfolioSettings: mappings(),
  error: null,
};

function flattenProviders(
  portfolios: Array<CompositePortfolioModel>,
): Array<string> {
  const flatArray: Array<string> = [];

  portfolios.forEach((portfolio) => {
    portfolio.keys.forEach((k: string) => {
      flatArray.push(k);
    });
  });
  return flatArray;
}

const getters = {
  providers: (state) => flattenProviders(state.compositePortfolios),
  displayLength: (state) => state.displayLength,
  compositePortfolios: (state) => state.compositePortfolios,
  portfolioLoadingStatus: (state) => state.portfolioLoadingStatus,
};

// const helpers = {
// };

const actions = {
  async addNewCompositePortfolio({ commit, getters }, data) {
    // check that we don't already have a portfolio with this name
    const existingIndex = getters.compositePortfolios.findIndex(
      (item) => item.name === data.name,
    );
    if (existingIndex !== -1) {
      throw new Error(`Portfolio ${data.name} already exists!`);
    }
    const newPortfolio: CompositePortfolioModel = new CompositePortfolioModel({
      name: data.name,
      holdings: [],
      cash: { currency: "$", value: 0.0 },
      target_size: data.target_size,
      components: [],
      refreshed_at: Math.floor(Date.now() / 1000),
      profit_or_loss: 0.0,
      profit_or_loss_v2: {
        dividends: { currency: "$", value: 0.0 },
        appreciation: { currency: "$", value: 0.0 },
      },
      appreciation: { currency: "$", value: 0.0 },
      dividends: { currency: "$", value: 0.0 },
    });
    commit("addCompositePortfolios", newPortfolio);
    commit("savePortfolio");
  },
  async setDisplayLength({ commit }, data) {
    commit("setDisplayLength", data);
  },
  async setCompositePortfolios({ commit }, data) {
    commit("setCompositePortfolios", data);
  },
  async pushEmptyProvider({ commit }, data) {
    commit("pushNewProvider", data);
  },
  async removeProvider({ commit }, data) {
    commit("removeProvider", data);
  },
  async removeCompositePortfolio({ commit }, data) {
    commit("removeCompositePortfolio", data);
    commit("savePortfolio");
  },
  async setPortfolioSize({ commit }, data) {
    commit("setPortfolioSize", data);
    commit("savePortfolio");
  },
  async refreshCompositePortfolio({ commit, getters, actions }, data) {
    const portfolioName = data.portfolioName;
    let keys = data.keys;
    const existingIndex = getters.compositePortfolios.findIndex(
      (item) => item.name === data.portfolioName,
    );
    const existing = getters.compositePortfolios[existingIndex];
    if (existingIndex === -1) {
      throw new Error(`Portfolio ${portfolioName} not found`);
    }
    if (!keys) {
      keys = existing.keys;
    }
    commit("setPortfolioLoadingStatus", {
      name: portfolioName,
      status: true,
      error: null,
    });
    const args = {
      key: portfolioName,
      providers: keys,
      providers_to_refresh: keys,
    };
    try {
      const response = await instance.post(`composite_portfolio/refresh`, args);

      const parsed = new CompositePortfolioModel(response.data);
      // this is information that is only available locally
      parsed.target_size = existing.target_size;
      commit("updateCompositePortfolio", parsed);
      commit("setPortfolioLoadingStatus", false);
      commit("savePortfolio");
    } catch (error) {
      let errorString = "error refreshing";
      if (error instanceof Error) {
        errorString = error.toString();
      }
      commit("setPortfolioLoadingStatus", {
        name: portfolioName,
        status: false,
        error: errorString,
      });
      keys.forEach((element, _) => {
        actions.probeLogin({ provider: element, loggedIn: false });
      });
      throw error;
    }
  },
  async refreshCompositePortfolios({ commit, getters }) {
    commit("setPortfolioLoadingStatus", { name: null, status: true });
    try {
      const response = await instance.get(`composite_portfolios`);
      response.data.forEach((element, _) => {
        const newPortfolio: CompositePortfolioModel =
          new CompositePortfolioModel(element);
        const existingIndex = state.compositePortfolios.findIndex(
          (item) => item.name === element.name,
        );
        if (existingIndex === -1) {
          commit("addCompositePortfolios", newPortfolio);
        } else {
          const current = state.compositePortfolios[existingIndex];
          this.refreshCompositePortfolio(
            { commit, getters },
            { portfolioName: current.name, keys: current.keys },
          );
        }
      });
      commit("setPortfolioLoadingStatus", false);
      commit("savePortfolio");
    } catch (error) {
      commit("setError", error);
      commit("setPortfolioLoadingStatus", { name: null, status: false });

      return;
    }
  },
  async saveCompositePortfolios({ commit }) {
    commit("savePortfolio");
  },
  async loadCompositePortfolios({ commit }) {
    const data = storageAPI.getPortfolios();
    commit("loadPortfolios", data);
  },
};

const mutations = {
  setDisplayLength(state, data) {
    state.displayLength = data;
  },
  setCompositePortfolios(state, data) {
    state.compositePortfolios = data;
  },
  addCompositePortfolios(state, data) {
    state.compositePortfolios.push(data);
  },
  removeCompositePortfolio(state, data) {
    state.compositePortfolios = state.compositePortfolios.filter(
      (item) => item.name !== data.portfolioName,
    );
  },
  setPortfolioSize(state, data) {
    const existingIndex = state.compositePortfolios.findIndex(
      (item) => item.name === data.portfolioName,
    );
    state.compositePortfolios[existingIndex].target_size = data.size;
  },
  setPortfolioLoadingStatus(state, data) {
    if (!data.name) {
      state.portfolioLoadingStatus = data.status;
    } else {
      const existingIndex = state.compositePortfolios.findIndex(
        (item) => item.name === data.name,
      );
      state.compositePortfolios[existingIndex].components.forEach(
        (element, _) => {
          element.loading = data.status;
          if (data.error) {
            element.error = data.error;
          }
        },
      );
      state.compositePortfolios[existingIndex].loading = data.status;
      if (data.error) {
        state.compositePortfolios[existingIndex].error = data.error;
      }
    }
  },
  savePortfolio(state) {
    storageAPI.setPortfolios(state.compositePortfolios);
  },
  loadPortfolios(state, data) {
    state.compositePortfolios = data;
  },
  setError(state, data) {
    state.error = data;
  },
  removeProvider(state, data) {
    const existingIndex = state.compositePortfolios.findIndex(
      (item) => item.name === data.portfolioName,
    );
    if (existingIndex === -1) {
      return;
    }
    const current = state.compositePortfolios[existingIndex];
    current.components = current.components.filter(
      (item) => item.provider !== data.provider,
    );
    current.keys = current.keys.filter((item) => item !== data.provider);
  },
  pushNewProvider(state, data) {
    const existingIndex = state.compositePortfolios.findIndex(
      (item) => item.name === data.portfolioName,
    );
    if (existingIndex === -1) {
      return;
    }
    const current = state.compositePortfolios[existingIndex];
    if (data.key in current.keys) {
      return;
    }
    current.keys.push(data.key);
    const newSub = new SubPortfolioModel({
      provider: data.key,
      name: data.key,
      target_size: 0,
      holdings: [],
      cash: { currency: "$", value: 1000.0 },
      profit_or_loss: { currency: "$", value: 0.0 },
      profit_or_loss_v2: {
        dividends: { currency: "$", value: 0.0 },
        appreciation: { currency: "$", value: 0.0 },
      },
      dividends: { currency: "$", value: 0.0 },
      appreciation: { currency: "$", value: 0.0 },
    });
    newSub.loading = true;
    current.components.push(newSub);
    state.compositePortfolios[existingIndex] = current;
  },
  updateCompositePortfolio(state, data) {
    const existingIndex = state.compositePortfolios.findIndex(
      (item) => item.name === data.name,
    );

    // If an existing element is found, replace it with the new element
    if (existingIndex !== -1) {
      state.compositePortfolios[existingIndex] = data;
    } else {
      // Otherwise, append the new element to the array
      state.compositePortfolios.push(data);
    }
  },
};

export default {
  state,
  getters,
  actions,
  mutations,
};
