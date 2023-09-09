import Store from 'electron-store';
import instance from '/src/api/instance'
import TargetPortfolioModel from '/src/models/TargetPortfolioModel';
import TargetPortfolioElementModel from '/src/models/TargetPortfolioElementModel';

const store = new Store<Record<string, Object>>({
    name: 'indexes',
    watch: true,
});

const storageKey = 'customIndexes'
const storageAPI = {
    setCustomIndexes(value: Array<any>) {
        // const buffer = safeStorage.encryptString(value);
        store.set(storageKey, value);
        // store.set(key, buffer.toString(encoding));
    },


    getCustomIndexes(): Array<Object> {
        const data = store.get(storageKey, []) as Array<any>
        const parsed = data.map(dict => new TargetPortfolioModel(dict));
        return parsed
    },
};


const state = {
    indexes: [],
    customIndexes: storageAPI.getCustomIndexes()
};


const getters = {
    indexes: state => state.indexes,
    indexNames: state => state.indexes.map((item) => item.name).sort()

};


// const helpers = {
// };

const actions = {
    async loadIndexes({ commit, getters }) {
        if (getters.indexes.length > 0) {
            return
        }
        await instance.get('indexes_full').then((response) => {
            const keys = Object.keys(response.data.loaded);
            const indexes: Array<TargetPortfolioModel> = []
            for (const key of keys) {
                const element = response.data.loaded[key];
                const portfolioHoldings = element.holdings.map(
                    dict => new TargetPortfolioElementModel(dict));
                const targetPortfolio = new TargetPortfolioModel({
                    'holdings': portfolioHoldings,
                    'source_date': element.source_date,
                    'name': key
                });
                indexes.push(targetPortfolio)
            }

            commit('setIndexes', indexes)
        });
    }
};



const mutations = {
    setIndexes(state, indexes ) {
        state.indexes = indexes

    }
};


export default {
    state,
    getters,
    actions,
    mutations
};
