import { createRouter, createWebHashHistory } from "vue-router";
import CompositePortfolioView from "/src/views/CompositePortfolioView.vue";
import PortfolioListView from "../views/PortfolioListView.vue";
import LoadingView from "../views/LoadingView.vue";

const routes = [
  {
    path: "/",
    name: "loading",
    component: LoadingView,
  },
  {
    path: "/composite_portfolio/:portfolioName",
    name: "composite_portfolio",
    props: true, // Pass route.params as props to the component
    component: CompositePortfolioView,
    // route level code-splitting
    // this generates a separate chunk (about.[hash].js) for this route
    // which is lazy-loaded when the route is visited.
    // component: () => import(/* webpackChunkName: "about" */ '../views/AboutView.vue')
  },
  {
    path: "/portfolio_list",
    name: "portfolio_list",
    component: PortfolioListView,
    // route level code-splitting
    // this generates a separate chunk (about.[hash].js) for this route
    // which is lazy-loaded when the route is visited.
    // component: () => import(/* webpackChunkName: "about" */ '../views/AboutView.vue')
  },
];

const router = createRouter({
  history: createWebHashHistory(),
  routes,
});

export default router;
