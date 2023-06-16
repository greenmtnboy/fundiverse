<template>
  <v-list density = "compact" v-if="portfolio.holdings.length>0">
    <template  v-for="(element, i) in sortedPortfolio" :key="i">
      <PortfolioElement :element="element" :totalPortfolioSize="targetSize" />
    </template>
  </v-list>
</template>
  
<script>
import PortfolioElement from "./PortfolioElement.vue";
import PortfolioModel from '../models/PortfolioModel';

export default {
  name: "PortfolioView",
  components: {
    PortfolioElement,
  },
  computed: {
    // portfolioSum() {
    //   return this.portfolio.holdings.reduce((sum, holding) => sum + holding.value.value, 0);
    // },
    sortedPortfolio() {
      let local_list = this.portfolio.holdings;
      local_list.sort((a, b) => b.value.value - a.value.value)
      return local_list;
    },
  },
  props: {
    portfolio: {
      type: PortfolioModel,
      required: true,
    },
    targetSize: {
      type: Number,
      required: false,
    },
  },
};
</script>