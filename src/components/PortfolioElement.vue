<template>
    <main>
        <v-list-item class="card-body">
          <div class="card-text">{{ element.ticker }} {{element.value.currency}}{{element.value.value}}</div>
    </v-list-item>
    </main>
  </template>
  <script>
  import PortfolioElementModel from  '../models/PortfolioElementModel';

  export default {
    name: "PortfolioElement",
    props: {
      element: {
        type: PortfolioElementModel,
        required: true,
      },
    },
  };
  </script>