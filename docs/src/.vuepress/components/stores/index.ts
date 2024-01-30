import { createStore } from 'vuex'
import { exports } from './modules/demo'

export const store = createStore({
    // state: {
    // },
    // getters: {
    // },
    // mutations: {
    // },
    // actions: {
    // },
    modules: {
        exports
    }
})


