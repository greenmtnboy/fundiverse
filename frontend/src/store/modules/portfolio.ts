import Store from "electron-store";
import { reactive } from "vue";
import CompositePortfolioModel from "/src/models/CompositePortfolioModel";
import instance from "/src/api/instance";
import apiHelpers from "/src/api/helpers";
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
    // persist immediately - the post-login refresh also saves, but only on
    // success, and a failed refresh should not lose the added provider
    commit("savePortfolio");
  },
  async removeProvider({ commit }, data) {
    commit("removeProvider", data);
    commit("savePortfolio");
  },
  async removeCompositePortfolio({ commit }, data) {
    commit("removeCompositePortfolio", data);
    commit("savePortfolio");
  },
  async setPortfolioSize({ commit }, data) {
    commit("setPortfolioSize", data);
    commit("savePortfolio");
  },
  /**
   * Refresh a composite portfolio, tolerating providers we are not logged
   * into.
   *
   * By default the backend fetches live data for every authenticated
   * provider and serves the rest from cache, so dropping money into one
   * brokerage and hitting refresh works without re-authenticating everything.
   * Pass `providersToRefresh` to narrow it further; pass `requireAll` to get
   * the old fail-if-anything-is-missing behaviour.
   */
  async refreshCompositePortfolio({ commit, getters, dispatch }, data) {
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
    // accept either spelling; callers previously passed keys_to_refresh and it
    // was silently ignored
    const providersToRefresh =
      data.providersToRefresh ?? data.keys_to_refresh ?? null;
    commit("setPortfolioLoadingStatus", {
      name: portfolioName,
      status: true,
      error: null,
      providers: providersToRefresh,
    });
    const args = {
      key: portfolioName,
      providers: keys,
      // null means "everything we can actually reach" - the partial default
      providers_to_refresh: providersToRefresh,
      require_all: data.requireAll ?? false,
      // our locally persisted holdings outlive the backend's in-memory cache,
      // so replay them for anything the backend cannot fetch itself
      cached: existing.cachedSnapshots(),
    };
    try {
      const response = await instance.post(`composite_portfolio/refresh`, args);

      const parsed = new CompositePortfolioModel(response.data);
      // this is information that is only available locally
      parsed.target_size = existing.target_size;
      commit("mergeCompositePortfolio", parsed);
      commit("setPortfolioLoadingStatus", {
        name: portfolioName,
        status: false,
      });
      commit("savePortfolio");
      // the response is authoritative about which providers we could reach, so
      // use it to keep the auth store in sync without extra probe calls
      response.data.components &&
        Object.values(response.data.components).forEach((component: any) => {
          dispatch("setProviderState", {
            provider: component.provider,
            loggedIn: component.status !== "unauthenticated",
          });
        });
      return parsed;
    } catch (error) {
      let errorString = "error refreshing";
      if (error instanceof Error) {
        // prefer the backend's detail message (e.g. the underlying provider
        // API error) over the generic "FetchError: status 422" string
        errorString = apiHelpers.getErrorMessage(error);
      }
      commit("setPortfolioLoadingStatus", {
        name: portfolioName,
        status: false,
        error: errorString,
      });
      keys.forEach((element, _) => {
        dispatch("probeLogin", { provider: element });
      });
      throw error;
    }
  },
  async refreshCompositePortfolios({ commit, dispatch }) {
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
          dispatch("refreshCompositePortfolio", {
            portfolioName: current.name,
            keys: current.keys,
          });
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
      return;
    }
    const existingIndex = state.compositePortfolios.findIndex(
      (item) => item.name === data.name,
    );
    if (existingIndex === -1) {
      return;
    }
    const portfolio = state.compositePortfolios[existingIndex];
    // a partial refresh only spins the providers it is actually touching;
    // `providers` of null means "whichever ones the backend can reach"
    const scoped = data.providers ?? null;
    portfolio.components.forEach((element, _) => {
      if (scoped && !scoped.includes(element.provider)) {
        return;
      }
      element.loading = data.status;
      if (data.error) {
        element.error = data.error;
      } else if (data.status) {
        element.error = null;
      }
    });
    portfolio.loading = data.status;
    if (data.error) {
      portfolio.error = data.error;
    } else if (data.status) {
      portfolio.error = null;
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
    if (current.keys.includes(data.key)) {
      return;
    }
    current.keys.push(data.key);
    const newSub = new SubPortfolioModel({
      provider: data.key,
      name: data.key,
      target_size: 0,
      holdings: [],
      // a placeholder until the first refresh reports real numbers
      cash: { currency: "$", value: 0.0 },
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
  /**
   * Fold a refresh result into what we already have.
   *
   * A partial refresh only speaks for the providers it touched, so providers
   * absent from the response keep their previously known holdings rather than
   * being wiped. Providers the user added but never logged into also survive.
   */
  mergeCompositePortfolio(state, data) {
    const existingIndex = state.compositePortfolios.findIndex(
      (item) => item.name === data.name,
    );
    if (existingIndex === -1) {
      state.compositePortfolios.push(data);
      return;
    }
    const existing = state.compositePortfolios[existingIndex];
    const incoming = new Map<string, SubPortfolioModel>(
      data.components.map((component: SubPortfolioModel) => [
        component.provider,
        component,
      ]),
    );

    // preserve the user's ordering of providers, then append any new ones
    const merged = existing.components.map((component) => {
      const update = incoming.get(component.provider);
      incoming.delete(component.provider);
      if (!update) {
        return component;
      }
      update.loading = false;
      return update;
    });
    data.components.forEach((component) => {
      if (incoming.has(component.provider)) {
        merged.push(component);
      }
    });

    data.components = reactive(merged);
    data.keys = reactive(merged.map((component) => component.provider));
    data.loading = false;
    data.error = null;
    state.compositePortfolios[existingIndex] = data;
  },
};

export default {
  state,
  getters,
  actions,
  mutations,
};
