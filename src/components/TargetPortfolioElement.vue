<template>
        
        <v-list-item class="card-body">
          <div class="card-text">{{ element.ticker }} {{elementWeight}}%</div>
          <!-- <v-row> {{ elementWeight }}%</v-row> -->
    </v-list-item>
  </template>
  <script>
  import TargetPortfolioElementModel from  '../models/TargetPortfolioElementModel';

  export default {
    name: "TargetPortfolioElement",
    props: {
      element: {
        type: TargetPortfolioElementModel,
        required: true,
      },
    },
    computed: {
      elementWeight() {
        return Math.round(this.element.weight*10000)/100;
      },
    }
  };
  </script>