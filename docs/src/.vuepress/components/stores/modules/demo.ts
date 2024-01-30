import TargetPortfolioModel from '../../models/TargetPortfolioModel';
import TargetPortfolioElementModel from '../../models/TargetPortfolioElementModel';
import PortfolioCustomization from '../../models/PortfolioCustomization';
import ListModification from '../../models/ListModification';
import StockModification from '../../models/StockModification';

import { instance } from '../../api/instance'

const storageAPI = {
    getPortfolio(): TargetPortfolioModel {
        let port = new TargetPortfolioModel({
            holdings: [
            ],
            source_date: '2023-01-01',
            name: 'test',
        })
        return port
    },
    getCustomization() {
        return new PortfolioCustomization({
            reweightIndex: true,
            indexPortfolio: null,
            excludedLists: new Set(), excludedTickers: new Set(),
            stockModifications: [], listModifications: []
        })
    }
}

const state = {
    demoPortfolio: storageAPI.getPortfolio(),
    portfolioTarget: 100_000,
    stockLists: {},
    indexes: {},
    customization: storageAPI.getCustomization(),
};


const getters = {
    demoPortfolio: state => state.demoPortfolio,
    portfolioTarget: state => state.portfolioTarget,
    stockLists: state => state.stockLists,
    indexes: state => state.indexes,
    portfolioCustomization: state => state.customization,
};

const actions = {
    async setPortfolioSize({ commit }, data) {
        commit('setPortfolioSize', data)
    },
    async getIndexes({ commit }) {
        const data = await instance.get('/indexes_full')
        commit('setIndexes', data.data.loaded)
    },
    async getStockLists({ commit }) {
        const data = await instance.get('/stock_lists')
        commit('setStockLists', data.data.loaded)
    },
    async setPortfolioTargetIndex({ commit }, data) {
        if (!data.index) {
            return
        }
        commit('setPortfolioTargetIndex', data)
        commit('saveCustomizations')
    },
    async excludeStock({ commit }, data) {
        commit('excludeStock', data)
        commit('saveCustomizations')
    },
    async removeStockExclusion({ commit }, data) {
        commit('removeStockExclusion', data)
        commit('saveCustomizations')
    },
    async modifyStock({ commit }, data) {
        commit('modifyStock', data)
        commit('saveCustomizations')
    },
    async removeStockModification({ commit }, data) {
        commit('removeStockModification', data)
        commit('saveCustomizations')
    },

    async excludeList({ commit }, data) {
        commit('excludeList', data)
        commit('saveCustomizations')
    },
    async removeListExclusion({ commit }, data) {
        commit('removeListExclusion', data)
        commit('saveCustomizations')
    },

    async modifyList({ commit }, data) {
        commit('modifyList', data)
        commit('saveCustomizations')
    },
    async saveCustomizations({ commit },) {
        commit('saveCustomizations')
    },
    // async loadCustomizations({ commit }) {
    //     const data = storageAPI.getDefaults()
    //     commit('commitCustomizations', data)
    // },
    // async loadDefaultModifications({ commit }) {
    //     commit('loadDefaults', storageAPI.getDefaults())
    // },
    async clearAllModifications({ commit }) {
        commit('clearAllModifications')
    }
};

const mutations = {
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
        customization.excludedTickers.add(data.ticker)
    },
    removeStockExclusion(state, data) {
        const customization = state.customization;
        if (data.mode === 'exclusion') {
            customization.excludedTickers.delete(data.ticker)
        }
        else if (data.mode === 'modification') {
            customization.stockModifications = customization.stockModifications.filter(item => item.ticker !== data.ticker)
        }

    },
    modifyStock(state, data) {
        const customization = state.customization;
        customization.stockModifications.push(new StockModification(data.ticker, data.scale))
    },
    removeStockModification(state, data) {
        const customization = state.customization;
        customization.stockModifications = customization.stockModifications.filter(item => item.ticker !== data.ticker)
    },
    excludeList(state, data) {
        const customization = state.customization;
        customization.excludedLists.add(data.list)
    },
    removeListExclusion(state, data) {
        const customization = state.customization;
        customization.excludedLists.delete(data.list)
    },
    modifyList(state, data) {
        // push the entire object here
        const customization = state.customization;
        customization.listModifications = customization.listModifications.filter(item => item.list !== data.list)
        customization.listModifications.push(new ListModification(data.list, data.scale))
    },
    removeListModification(state, data) {
        const customization = state.customization;
        customization.listModifications = customization.listModifications.filter(item => item.list !== data.list)
    },
    // loadDefaults(state, data) {
    //     if (data === undefined) return

    //     state.customizations = data
    // },
    clearAllModifications(state, data) {
        const customization = state.customization;
        customization.listModifications = []
        customization.stockModifications = []
        customization.excludedLists = new Set()
        customization.excludedTickers = new Set()
    },
    setPortfolioTargetIndex(state, data) {
        const customization = state.customization;
        customization.indexPortfolio = data.index
        state.demoPortfolio = state.indexes[data.index]
    }
};

export const exports = {
    state,
    getters,
    actions,
    mutations
}
