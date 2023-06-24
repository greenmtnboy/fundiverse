const state = {
    displayLength:50
};

const getters = {
    displayLength: state => state.displayLength
};


// const helpers = {
// };

const actions = {
    async setDisplayLength({ commit }, data) {
        commit('setDisplayLength', data)
    },
};



const mutations = {
    setDisplayLength(state, data) {
        state.displayLength = data;
    }
};


export default {
    state,
    getters,
    actions,
    mutations
};
