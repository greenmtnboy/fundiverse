

import store from '@/store/local';
import PortfolioCustomization from '@/models/PortfolioCustomization';
import StockModification from '@/models/StockModification';
import instance from '@/api/instance'
function isObjectEmpty(obj) {
    if (!obj) {
        return true;
    }
    return Object.keys(obj).length === 0;
}
const storageAPI = {
    setDefaults(value) {
        const final: Array<any> = []
        value.forEach((val, key) => {
            const destructured = {...val}
            destructured.excludedLists = Array.from(destructured.excludedLists)
            destructured.excludedTickers = Array.from(destructured.excludedTickers)
            final.push({ key: key, value: destructured })
        })
        store.set('customizations', final);
    },

    getDefaults() {
        const dat: Array<any> = ((store.get('customizations') as unknown) as Array<any>)
        const final = new Map()
        dat.forEach((item) => {
            if (isObjectEmpty(item.value.excludedLists)) {
                item.value.excludedLists = new Set()
            }
            else {  
                item.value.excludedLists = new Set(item.value.excludedLists)
            }
            if (isObjectEmpty(item.value.excludedTickers)) {
                item.value.excludedTickers = new Set()
            }
            else {
                item.value.excludedTickers = new Set(item.value.excludedTickers)
            }
            final.set(item.key, new PortfolioCustomization(item.value))
        })
        return final
    }
};

function customizationDefault(): Map<String, PortfolioCustomization> {
    return new Map()
}

const state = {
    customizations: customizationDefault(),
    stockLists: []
    // excludedTickers: new Set(),
    // excludedLists: new Set(),
    // stockModifications: [],
    // listModifications: [],
    // stockLists: {} // {list_name: [ticker1, ticker2, ...]}
};


const getters = {
    portfolioCustomizations: state => state.customizations,
    // excludedTickers: state => state.excludedTickers,
    // excludedLists: state => state.excludedLists,
    // stockModifications: state => state.stockModifications,
    // listModifications: state => state.listModifications,
    stockLists: state => state.stockLists,
    // totalModifications: state => state.stockModifications.length + state.listModifications.length + state.excludedLists.size + state.excludedTickers.size,
};


// const helpers = {
// };

const actions = {
    async getStockLists({ commit }) {
        await instance.get('stock_lists').then((response) => {
            commit('setStockLists', { stockLists: response.data.loaded, })
        });
    },

    async setStockLists({ commit }, data) {
        commit('setStockLists', data)
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
        // commit('saveDefaults')
    },
    async loadCustomizations({ commit }) {
        const data = storageAPI.getDefaults()
        commit('commitCustomizations', data)
    },
    async loadDefaultModifications({ commit }) {
        commit('loadDefaults', storageAPI.getDefaults())
    },
    async clearAllModifications({ commit }) {
        commit('clearAllModifications')
    }
};

function safeGetCustomization(state, name: String) {
    if (!name) {
        throw new Error('No name provided for customization')
    }
    const customization = state.customizations.get(name)
    if (customization) {
        return customization
    }
    const newPortfolio = new PortfolioCustomization({
        reweightIndex: true,
        indexPortfolio: 'sp500_2023_q3',
        excludedLists: new Set(), excludedTickers: new Set(),
        stockModifications: [], listModifications: []
    });
    state.customizations.set(name, newPortfolio)
    return newPortfolio

}


const mutations = {
    setStockLists(state, data) {
        state.stockLists = data.stockLists
    },
    excludeStock(state, data) {
        const customization = safeGetCustomization(state, data.portfolioName);
        customization.excludedTickers.add(data.ticker)
    },
    removeStockExclusion(state, data) {
        safeGetCustomization(state, data.portfolioName).excludedTickers.delete(data.ticker)
    },
    modifyStock(state, data) {
        safeGetCustomization(state, data.portfolioName).stockModifications.push(new StockModification(data.ticker, data.scale))
    },
    removeStockModification(state, data) {
        const customization = safeGetCustomization(state, data.portfolioName)
        customization.stockModifications = customization.stockModifications.filter(item => item.ticker !== data.ticker)
    },
    excludeList(state, data) {
        safeGetCustomization(state, data.portfolioName).excludedLists.add(data.list)
    },
    removeListExclusion(state, data) {
        safeGetCustomization(state, data.portfolioName).excludedLists.delete(data.list)
    },
    modifyList(state, data) {
        safeGetCustomization(state, data.portfolioName).listModifications.push(data.ticker)
    },
    removeListModification(state, data) {
        const customization = safeGetCustomization(state, data.portfolioName);
        customization.listModifications = customization.listModifications.filter(item => item.ticker !== data.ticker)
    },
    saveCustomizations(state) {
        console.log('saving customizations')
        storageAPI.setDefaults(state.customizations)
        console.log(state.customizations)
        console.log('checking what we saved')
        const recovered = storageAPI.getDefaults()
        console.log(recovered)
    },
    commitCustomizations(state, data) {
        if (data === undefined) return
        state.customizations = data
    },
    // loadDefaults(state, data) {
    //     if (data === undefined) return

    //     state.customizations = data
    // },
    clearAllModifications(state, data) {
        const customization = safeGetCustomization(state, data.portfolioName)
        customization.listModifications = []
        customization.stockModifications = []
        customization.excludedLists = new Set()
        customization.excludedTickers = new Set()
    }
};


export default {
    state,
    getters,
    actions,
    mutations
};
