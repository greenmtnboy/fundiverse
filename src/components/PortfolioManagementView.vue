<template>
  <div id="app">
    <div class="container">
      <div class="text-center">
        <h2 class="text-center mt-5">Make Index Funds 🍿</h2>
        <p>Click buttons, buy stocks.</p>
      </div>
      <v-btn class="my-4" @click="getPortfolio()">Get Current Portfolio
      </v-btn>
      <v-btn class="my-4" @click="buyIndex()">
        Buy 50 Dollars of Index
      </v-btn>
      <v-row><v-col cols=6> <v-card>
            <v-card-title>Owned Portfolio</v-card-title>
            <v-card-text>           <PortfolioView :portfolio="portfolio" /></v-card-text>
 
          </v-card></v-col><v-col cols=6></v-col></v-row>

    </div>
  </div>
</template>

<script>
import PortfolioView from "./PortfolioView.vue"
import PortfolioModel from '../models/PortfolioModel';
import PortfolioElementModel from '../models/PortfolioElementModel';
import axios from 'axios';

export default {
  name: "App",
  components: {
    PortfolioView,
  },
  data() {
    return {
      portfolio: new PortfolioModel([]),

    };
  },
  methods: {

    getPortfolio() {
      return axios.get('http://localhost:3000/portfolio').then((response) => {
        const portfolioHoldings = response.data.holdings.map(dict => new PortfolioElementModel(dict));
        this.portfolio = new PortfolioModel(portfolioHoldings);
        console.log(this.portfolio)
      });
    },

    buyIndex() {
      return axios.post('http://localhost:3000/buy_index').then(() => {
        this.getPortfolio();
      });
    },
  },
  mounted() {
    this.getPortfolio()
  },
};
</script>