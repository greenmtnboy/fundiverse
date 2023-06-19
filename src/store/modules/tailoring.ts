


const state = {
    excludedTickers: new Set(),
    excludedLists: new Set(),
    lists:{} // {list_name: [ticker1, ticker2, ...]}
};

const getters = {
    excludedTickers: state => new Set([...state.excludedTickers]),
    excludedLists: state => state.excludedLists
};


// const helpers = {
// };

const actions = {
    async setLists({ commit }, data) {
        commit('setLists', data)
    },
    async excludeStock({ commit }, data) {
        commit('excludeStock', data)
    },
    async excludeList({ commit }, data) {
        commit('excludeList', data)
    },
};



const mutations = {
    setLists(state, data) {
        state.lists = data
    },
    excludeStock(state, data) {
        state.excludedTickers.add(data)
    }
};


export default {
    state,
    getters,
    actions,
    mutations
};
