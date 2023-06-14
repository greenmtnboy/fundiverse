<template>
  <v-list class="row" v-if="portfolio.holdings.length>0">
    <div class="col-md-3" v-for="(element, i) in portfolio.holdings" :key="i">
      <PortfolioElement :element="element" />
    </div>
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
  props: {
    portfolio: {
      type: PortfolioModel,
      required: true,
    },
  },
};
</script>