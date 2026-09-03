// const { safeStorage } = require("electron");
import store from "/src/store/local";
import instance from "/src/api/instance";

const storageAPI = {
  setCredential(key: string, value: string) {
    // const buffer = safeStorage.encryptString(value);
    store.delete(key);
    store.set(key, value);
    // store.set(key, buffer.toString(encoding));
  },

  deletePassword(key: string) {
    store.delete(key);
  },

  getCredentials(): Array<{ key: string; value: string }> {
    return Object.entries(store.store).reduce(
      (credentials, [key, buffer]) => {
        //   return [...credentials, { key, value: safeStorage.decryptString(Buffer.from(buffer, 'latin1')) }];
        return [...credentials, { key, value: buffer }];
      },
      [] as Array<{ key: string; value: string }>,
    );
  },
};

const state = {
  loggedIn: false,
  // keys: [],
  keys: storageAPI.getCredentials(),
  activeProviders: [],
  providerRefreshedAt: {},
};

const getters = {
  isLoggedIn: (state) => state.loggedIn,
  keys: (state) => state.keys,
  activeProviders: (state) => state.activeProviders,
  providerRefreshedAt: (state) => state.providerRefreshedAt,
  isProviderActive: (state) => (provider: string) =>
    state.activeProviders.includes(provider),
};

// const helpers = {
// };

const actions = {
  async probeLogin({ commit }, data) {
    try {
      const response = await instance.get(`/logged_in/${data.provider}`);
      await actions.setProviderState(
        { commit },
        { provider: data.provider, loggedIn: Boolean(response.data) },
      );
    } catch {
      await actions.setProviderState(
        { commit },
        { provider: data.provider, loggedIn: false },
      );
    }
  },
  /**
   * Refresh the auth state of every provider in one call.
   *
   * Cheaper than probing providers individually, and it is what lets the UI
   * show up front which providers a partial operation will actually reach.
   */
  async probeAllLogins({ commit }) {
    try {
      const response = await instance.get(`/provider_status`);
      commit("setAllProviderStates", response.data.providers);
    } catch {
      // leave the last known state alone; the backend may still be starting
    }
  },
  async setProviderState({ commit }, data) {
    commit("setProviderState", {
      provider: data.provider,
      loggedIn: data.loggedIn,
    });
  },
  async setLoggedIn({ commit }, data) {
    commit("login", data);
  },
  async storeSavedValue({ commit }, data) {
    commit("storeCredential", data);
  },

  async setLoggedOut({ commit }) {
    commit("logout");
  },
};

const mutations = {
  login(state, _) {
    state.loggedIn = true;
    // state.provider = data.provider;
  },
  logout(state) {
    state.loggedIn = false;
    // state.provider = '';
  },
  storeCredential(state, data) {
    storageAPI.setCredential(data.key, data.value);
    state.keys.push(data);
  },
  setAllProviderStates(state, providers) {
    state.activeProviders = providers
      .filter((entry) => entry.authenticated)
      .map((entry) => entry.provider);
    state.providerRefreshedAt = providers.reduce((acc, entry) => {
      acc[entry.provider] = entry.refreshed_at;
      return acc;
    }, {});
  },
  setProviderState(state, data) {
    if (data.loggedIn) {
      const index = state.activeProviders.indexOf(data.provider);
      if (index === -1) {
        state.activeProviders.push(data.provider);
      }
    } else {
      const index = state.activeProviders.indexOf(data.provider);
      if (index !== -1) {
        state.activeProviders.splice(index, 1);
      }
    }
  },
  // setProvider(state, data) {
  //     state.provider = data;
  // }
};

export default {
  state,
  getters,
  actions,
  mutations,
};
