import { createStore } from "vuex";
import auth from "./modules/auth";
import portfolio from "./modules/portfolio";
import tailoring from "./modules/tailoring";
import indexes from "./modules/indexes";
export default createStore({
  // state: {
  // },
  // getters: {
  // },
  // mutations: {
  // },
  // actions: {
  // },
  modules: {
    auth,
    portfolio,
    tailoring,
    indexes,
  },
});
