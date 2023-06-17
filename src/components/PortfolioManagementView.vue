<template>
  <div id="app">
    <div class="container">
      <div class="text-center">
        <h2 class="text-center mt-5">Fundiverse</h2>
        <p>Don't pick stocks. Picks lots of stocks.</p>
      </div>
      <v-row class="d-flex justify-center align-center pa-2">
        <v-col cols="6" class="d-flex justify-center align-center pa-2">
          <v-btn class="d-flex flex-column" @click="getPortfolio()">Refresh Portfolio

          </v-btn>
        </v-col>
        <v-col cols="6" class="d-flex justify-center align-center pa-2">
          <v-btn class="d-flex flex-column" @click="buyIndex()">
            Buy {{ toPurchase }} Dollars
          </v-btn>
        </v-col>
      </v-row>
      <v-row class="d-flex justify-center align-center pa-2">
        <v-col cols=6>
          <v-text-field variant="solo" label="Target Portfolio Size" v-model="portfolioTarget"
            :rules="numberValidationRules">
          </v-text-field>
        </v-col>
        <v-col cols=6>
          <v-text-field variant="solo" label="Purchase Amount" v-model="toPurchase" :rules="numberValidationRules">
          </v-text-field>
        </v-col>
      </v-row>
      <v-row><v-col cols=6> <v-card>
            <v-card-title style="min-height: 90px;" class="text-center">Owned Portfolio <v-progress-circular :size="35" :width="5"
                :model-value="portfolioPercentOfTarget" color="deep-orange-lighten-2"><span class="text-caption">{{
                  portfolioPercentOfTarget }}%</span></v-progress-circular></v-card-title>
                        <v-card-actions>
              <v-btn class="d-flex flex-column">Compare</v-btn>
            </v-card-actions>
            <v-card-text>
              <PortfolioView :portfolio="portfolio" :targetSize="portfolioTarget"/>
            </v-card-text>
          </v-card></v-col>
        <v-col cols=6>
          <v-card>
            <v-card-title style="min-height: 90px;" class="text-center">
              
              <v-select v-model="selectedIndex" :items="indexKeys" density="compact" variant="solo"
                label="Target Portfolio"></v-select>

            </v-card-title>
            <v-card-actions>
              <v-btn class="d-flex flex-column">Tailor</v-btn>
            </v-card-actions>
            <v-card-text>
              <TargetPortfolioView v-if="selectedIndex" :portfolio="targetPortfolio" />
            </v-card-text>
          </v-card>
        </v-col></v-row>

    </div>
  </div>
</template>

<script>
// Views
import PortfolioView from "./PortfolioView.vue"
import TargetPortfolioView from "./TargetPortfolioView.vue"

// Models
import PortfolioModel from '../models/PortfolioModel';
import PortfolioElementModel from '../models/PortfolioElementModel';
import TargetPortfolioModel from '../models/TargetPortfolioModel';
import TargetPortfolioElementModel from '../models/TargetPortfolioElementModel';
import TargetPortfolioListModel from '../models/TargetPortfolioListModel';

import axios from 'axios';

function parse_target_portfolio_element({ ticker, weight }) {
  return new TargetPortfolioElementModel({
    ticker: ticker,
    weight: weight,
  });
}

function parse_target_portfolio_model({ holdings, source_date }) {
  return new TargetPortfolioModel({ 'holdings': holdings.map(parse_target_portfolio_element), 'source_date': source_date });
}

export default {
  name: "App",
  components: {
    PortfolioView,
    TargetPortfolioView
  },
  data() {
    let map = new Map();
    return {
      portfolio: new PortfolioModel([]),
      targetPortfolios: new TargetPortfolioListModel({ 'loaded': map }),
      portfolioTarget: 100_000,
      toPurchase: 50,
      selectedIndex: null,
    };
  },
  computed: {
    targetPortfolio() {
      if (!this.selectedIndex) {
        return null
      }
      let output = this.targetPortfolios.loaded.get(this.selectedIndex);
      return output
    },
    portfolioSum() {
      return this.portfolio.holdings.reduce((sum, holding) => sum + holding.value.value, 0);
    },
    portfolioPercentOfTarget() {
      return Math.round((this.portfolioSum / this.portfolioTarget) * 100);
    },
    numberValidationRules() {
      return [
        (value) => {
          if (!value || /^[0-9\\.]+$/.test(value)) {
            return true;
          }
          return 'Only numbers are allowed.';
        }
      ];
    },
    indexKeys() {
      return Array.from(this.targetPortfolios.loaded.keys()).sort((a, b) => b.localeCompare(a));
    }
  },
  methods: {

    getPortfolio() {
      return axios.get('http://localhost:3000/portfolio').then((response) => {
        const portfolioHoldings = response.data.holdings.map(dict => new PortfolioElementModel(dict));
        this.portfolio = new PortfolioModel(portfolioHoldings);
      });
    },
    getIndexes() {
      return axios.get('http://localhost:3000/indexes').then((response) => {

        const transformedMap = new Map();

        Object.keys(response.data.loaded).forEach((key) => {
          const transformedValue = parse_target_portfolio_model(response.data.loaded[key])
          transformedMap.set(key, transformedValue);
        });
        this.targetPortfolios = new TargetPortfolioListModel({ loaded: transformedMap });
        this.selectedIndex = Array.from(this.targetPortfolios.loaded.keys())[0];
      });
    },
    // getStockLists() {
    //   return axios.get('http://localhost:3000/stock_lists').then((response) => {
    //     const portfolioHoldings = response.data.holdings.map(dict => new PortfolioElementModel(dict));
    //     this.portfolio = new StockListModel(portfolioHoldings);
    //   });
    // },

    buyIndex() {
      return axios.post('http://localhost:3000/buy_index',
      {'to_purchase': this.toPurchase, 'index':this.selectedIndex}).then(() => {
        this.getPortfolio();
      });
    },
  },
  mounted() {
    this.getPortfolio()
    this.getIndexes()
  },
};
</script>