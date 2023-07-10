import Store from 'electron-store';


const store = new Store<Record<string, Object>>({
    name: 'portfolios',
    watch: true,
});

const storageAPI = {
    setPortfolios(value: Object) {
        // const buffer = safeStorage.encryptString(value);
        store.set('compositePortfolios', value);
        // store.set(key, buffer.toString(encoding));
    },


    getPortfolios(): Array<Object> {
        return store.get('compositePortfolios', []) as Array<Object>
    },
};


const state = {
    displayLength:50,
    compositePortfolios: storageAPI
};

const getters = {
    displayLength: state => state.displayLength,
    compositePortfolios: state => state.compositePortfolios
};


// const helpers = {
// };

const actions = {
    async setDisplayLength({ commit }, data) {
        commit('setDisplayLength', data)
    },
    async setCompositePortfolios({ commit }, data) {
        commit('setCompositePortfolios', data)
    }
};



const mutations = {
    setDisplayLength(state, data) {
        state.displayLength = data;
    },
    setCompositePortfolios(state, data) {
        state.compositePortfolios=data;
    }
};


export default {
    state,
    getters,
    actions,
    mutations
};
