<template>
    <v-list class="pt-0" density = "compact"  v-if="portfolio.holdings.length>0">
      <template  v-for="(element, i) in sortedPortfolio" :key="i">
        <TargetPortfolioElement :element="element" />
      </template>
    </v-list>
  </template>
    
  <script>
  import TargetPortfolioElement from "./TargetPortfolioElement.vue";
  import TargetPortfolioModel from '../models/TargetPortfolioModel';
  
  export default {
    name: "TargetPortfolioView",
    components: {
      TargetPortfolioElement,
    },
    props: {
      portfolio: {
        type: TargetPortfolioModel,
        required: true,
      },
    },
    computed: {
        sortedPortfolio() {
            let local_list = this.portfolio.holdings;
            local_list.sort((a, b) => b.weight - a.weight);
            return local_list;
        },
    }
  };
  </script>