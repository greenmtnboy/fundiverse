<template>
    <v-progress-linear
        v-if="pythonLoading"
        color="primary"
        indeterminate
      ></v-progress-linear>
    <TargetPortfolioView
      v-else-if="demoPortfolio.holdings"
      :portfolio="demoPortfolio"
      :targetSize="portfolioTarget"
    >
    </TargetPortfolioView>
  </template>
  <style>
  .sharp {
    border-radius: 0;
  }
  </style>
  <script lang="ts">
  import TargetPortfolioView from "./target_portfolio/TargetPortfolioView.vue";
  import StockListSetter from "./target_portfolio/StockListSetter.vue";
  import IndexSetter from "./target_portfolio/IndexSetter.vue";
  import StockSetter from "./target_portfolio/StockSetter.vue";
  import { mapGetters, mapActions } from "vuex";
  
  export default {
    components: {
      TargetPortfolioView,
      StockListSetter,
      IndexSetter,
      StockSetter,
    },
    data() {
      return {
        activeSelector: "index",
      };
    },
    methods: {
      ...mapActions(["getStockLists", "getIndexes", "getPython"]),
    },
    computed: {
      ...mapGetters([
        "demoPortfolio",
        "portfolioTarget",
        "indexesLoading",
        "pythonLoading",
      ]),
    },
    mounted() {
    },
  };
  </script>
  