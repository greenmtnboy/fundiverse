import { safeStorage } from 'electron';
import Store from 'electron-store';

const store = new Store<Record<string, string>>({
  name: 'ray-encrypted',
  watch: true,
  encryptionKey: 'this_only_obfuscates',
});

const safeStorage =  {
  setPassword(key: string, password: string) {
    const buffer = safeStorage.encryptString(password);
    store.set(key, buffer.toString('latin1'));
  },

  deletePassword(key: string) {
    store.delete(key);
  },

  getCredentials(): Array<{ account: string; password: string }> {
    return Object.entries(store.store).reduce((credentials, [account, buffer]) => {
      return [...credentials, { account, password: safeStorage.decryptString(Buffer.from(buffer, 'latin1')) }];
    }, [] as Array<{ account: string; password: string }>);
  },
};
const state = {
    loggedIn: false
};

const getters = {
    isLoggedIn: state => state.loggedIn
};


// const helpers = {
// };

const actions = {
    async setLogin({ commit }) {
        commit('login')
    },
    async setLogOut({ commit }) {
        commit('logout')
    }

};



const mutations = {
    login(state,) {
        state.loggedIn = true;
    },
    logout(state,) {
        state.loggedIn = false;
    },
};


export default {
    state,
    getters,
    actions,
    mutations
};
