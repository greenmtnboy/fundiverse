

import store from '@/store/local';

const storageAPI = {
    setDefaults(value) {
        const storageObject = {
            listModifications: value.listModifications,
            stockModifications: value.stockModifications,
            excludedLists: [...value.excludedLists],
            excludedTickers: [...value.excludedTickers]
        }
        store.set('defaultModifications', storageObject);
    },


    getDefaults(){
        return store.get('defaultModifications')
    }
};

const state = {
    excludedTickers: new Set(),
    excludedLists: new Set(),
    stockModifications: [],
    listModifications: [],
    stockLists: {} // {list_name: [ticker1, ticker2, ...]}
};


const getters = {
    excludedTickers: state => state.excludedTickers,
    excludedLists: state => state.excludedLists,
    stockModifications: state => state.stockModifications,
    listModifications: state => state.listModifications,
    stockLists: state => state.stockLists,
    totalModifications: state => state.stockModifications.length + state.listModifications.length + state.excludedLists.size + state.excludedTickers.size,
};


// const helpers = {
// };

const actions = {
    async setStockLists({ commit }, data) {
        commit('setStockLists', data)
    },
    async excludeStock({ commit }, data) {
        commit('excludeStock', data)
    },
    async removeStockExclusion({ commit }, data) {
        commit('removeStockExclusion', data)
    },
    async modifyStock({ commit }, data) {
        commit('modifyStock', data)
    },
    async removeStockModification({ commit }, data) {
        commit('removeStockModification', data)
    },

    async excludeList({ commit }, data) {
        commit('excludeList', data)
    },
    async removeListExclusion({ commit }, data) {
        commit('removeListExclusion', data)
    },

    async modifyList({ commit }, data) {
        commit('modifyList', data)
    },
    async saveDefaultModifications({ commit }, ) {

        commit('saveDefaults')
    },
    async loadDefaultModifications({ commit }) {
        commit('loadDefaults', storageAPI.getDefaults())
    },
    async clearAllModifications({ commit }) {
        commit('clearAllModifications')
    }
};



const mutations = {
    setStockLists(state, data) {
        state.stockLists = data
    },
    excludeStock(state, data) {
        state.excludedTickers.add(data)
    },
    removeStockExclusion(state, data) {
        state.excludedTickers.delete(data)
    },
    modifyStock(state, data) {
        state.stockModifications.push(data)
    },
    removeStockModification(state, data) {
        state.stockModifications = state.stockModifications.filter(item => item.ticker !== data)
    },
    excludeList(state, data) {
        state.excludedLists.add(data)
    },
    removeListExclusion(state, data) {
        state.excludedLists.delete(data)
    },
    modifyList(state, data) {
        state.listModifications.push(data)
    },
    removeListModification(state, data) {
        state.listModifications = state.listModifications.filter(item => item.ticker !== data)
    },
    saveDefaults(state) {
        storageAPI.setDefaults(state)
    },
    loadDefaults(state, data) {
        if (data === undefined) return

        state.listModifications = data.listModifications
        state.stockModifications = data.stockModifications
        state.excludedLists = new Set(data.excludedLists)
        state.excludedTickers = new Set(data.excludedTickers)
    },
    clearAllModifications(state) {
        state.listModifications = []
        state.stockModifications = []
        state.excludedLists = new Set()
        state.excludedTickers = new Set()
    }
};


export default {
    state,
    getters,
    actions,
    mutations
};
