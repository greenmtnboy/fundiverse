<template>
  <v-list-item class="card-body">
    <div class="card-text">{{ element.ticker }} {{ element.value.currency }}{{ element.value.value }} ({{ elementWeight }}%)
    </div>
    <!-- <v-row> {{ elementWeight }}%</v-row> -->
  </v-list-item>
</template>
<script>
import PortfolioElementModel from '../models/PortfolioElementModel';

export default {
  name: "PortfolioElement",
  props: {
    element: {
      type: PortfolioElementModel,
      required: true,
    },
    totalPortfolioSize: {
      type: Number,
      required: false
    },
  },
  computed: {
    elementWeight() {
      if (!this.totalPortfolioSize) {
        return null;
      }
      return Math.round((this.element.value.value / this.totalPortfolioSize) * 10000) / 100;
    },
  }
};
</script>