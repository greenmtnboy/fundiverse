// const { safeStorage } = require("electron");
import store from '/src/store/local';
import instance from '/src/api/instance';

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
    activeProviders: [],
};

const getters = {
    isLoggedIn: state => state.loggedIn,
    keys: state => state.keys,
    activeProviders: state => state.activeProviders
};


// const helpers = {
// };

const actions = {
    async probeLogin({ commit }, data) {
        const response = await instance.get(`/logged_in/${data.provider}`)
        await actions.setProviderState({ commit }, { provider: data.provider, loggedIn: Boolean(response.data) })
    },
    async setProviderState({ commit }, data) {
        commit('setProviderState', { provider: data.provider, loggedIn: data.loggedIn })
    },
    async setLoggedIn({ commit }, data) {
        commit('login', data)
    },
    async storeSavedValue({ commit }, data) {
        commit('storeCredential', data)
    },

    async setLoggedOut({ commit },) {
        commit('logout')
    },


};



const mutations = {
    login(state, _) {
        state.loggedIn = true;
        // state.provider = data.provider;
    },
    logout(state,) {
        state.loggedIn = false;
        // state.provider = '';
    },
    storeCredential(state, data) {
        storageAPI.setCredential(data.key, data.value);
        state.keys.push(data)
    },
    setProviderState(state, data) {
        if (data.loggedIn) {
            const index = state.activeProviders.indexOf(data.provider);
            if (index === -1) {
                state.activeProviders.push(data.provider)
            }
        }
        else {

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
    mutations
};
