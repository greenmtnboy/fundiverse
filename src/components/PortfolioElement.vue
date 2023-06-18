<template>
  <v-list-item  :min-height="15">
    <div >{{ element.ticker }}<p class="text-medium-emphasis">{{ element.value.currency }}{{ element.value.value }} ({{ elementWeight }}%)</p>
    </div>
    <template v-slot:append>
      <v-btn  :loading="loading" 
       icon density="compact">
        <!-- <v-icon  :loading="loading" color="warning">mdi-cancel</v-icon> -->
      </v-btn>

    </template>
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