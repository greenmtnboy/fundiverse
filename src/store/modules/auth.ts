// const { safeStorage } = require("electron");
import Store from 'electron-store';



const store = new Store<Record<string, string>>({
    name: 'login-encrypted',
    watch: true,
    encryptionKey: 'this_is_always_accessible_by_user',
});

const storageAPI = {
    setCredential(key: string, value: string) {
        // const buffer = safeStorage.encryptString(value);
        store.set(key, value);
        // store.set(key, buffer.toString(encoding));
    },

    deletePassword(key: string) {
        store.delete(key);
    },

    getCredentials(): Array<{ key: string; value: string }> {
        return Object.entries(store.store).reduce((credentials, [key, buffer]) => {
            //   return [...credentials, { key, value: safeStorage.decryptString(Buffer.from(buffer, 'latin1')) }];
            return [...credentials, { key, value: buffer }];
        }, [] as Array<{ key: string; value: string }>);
    },
};

const state = {
    loggedIn: false,
    // keys: [],
    keys: storageAPI.getCredentials(),
};

const getters = {
    isLoggedIn: state => state.loggedIn,
    keys: state => state.keys

};


// const helpers = {
// };

const actions = {
    async setLoggedIn({ commit }) {
        commit('login')
    },
    async storeSavedValue({ commit }, data) {
        commit('storeCredential', data)
    },

    async setLoggedOut({ commit }) {
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
    storeCredential(state, data) {
        storageAPI.setCredential(data.key, data.value);
        state.keys.push(data)

    }
};


export default {
    state,
    getters,
    actions,
    mutations
};
