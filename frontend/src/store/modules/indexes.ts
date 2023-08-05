import Store from 'electron-store';
import instance from '@/api/instance'
import TargetPortfolioModel from '@/models/TargetPortfolioModel'
import TargetPortfolioElementModel from '@/models/TargetPortfolioElementModel'
const store = new Store<Record<string, Object>>({
    name: 'indexes',
    watch: true,
});

const storageAPI = {
    setPortfolios(value: Array<TargetPortfolioModel>) {
        // const buffer = safeStorage.encryptString(value);
        store.set('customIndexes', value);
        // store.set(key, buffer.toString(encoding));
    },


    getPortfolios(): Array<Object> {
        const data = store.get('customIndexes', []) as Array<any>
        const parsed = data.map(dict => new TargetPortfolioModel(dict));
        return parsed
    },
};

function defaults() {
    const data: Array<TargetPortfolioModel> = [];
    return data
}


const state = {
    indexes: []
};


const getters = {
    indexes: state => state.indexes,
    indexNames: state => state.indexes.map((item) => item.name)

};


// const helpers = {
// };

const actions = {
    async loadIndexes({ commit }) {
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
