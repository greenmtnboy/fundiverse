<template>
  <v-card>
    <v-card-title class="d-flex justify-center align-center">Portfolio Management</v-card-title>
    <v-row class="d-flex justify-center align-center px-2">
      <v-col cols=4>
        <v-text-field class="input-field" variant="solo" @input="handlePortfolioSizeInput" label="Target Portfolio Size"
          v-model="portfolioTarget" :rules="numberValidationRules">
        </v-text-field>
      </v-col>
      <v-col cols=4>
        <v-text-field class="input-field" variant="solo" label="Purchase Amount" v-model="toPurchase"
          :rules="numberValidationRules">
        </v-text-field>
      </v-col>
      <v-col cols="4">
        <v-text-field @update:modelValue="newValue => handlePortfolioSearchText(newValue)" class="input-field"
          label="Filter Tickers" variant="solo" v-model="searchQueryInternal" placeholder="AAPL" /></v-col>
    </v-row>
    <v-row>
      <v-col cols=6>
        <v-card>
          <v-card-title style="min-height: 90px;" class="text-center">Owned Portfolio
            <v-progress-linear color="blue-lighten-3" v-model="portfolioPercentOfTarget" height="15">
              <span class="text-caption">{{ portfolioPercentOfTarget }}%</span>
            </v-progress-linear>
          </v-card-title>
          <v-card-actions>
            <!-- <v-btn :loading="compareLoading" class="d-flex flex-column" @click="compareToIndex()">Compare</v-btn> -->
            <v-col cols="4" class="d-flex justify-center align-center px-2 py-0">
              <v-btn :loading="refreshLoading" class="d-flex flex-column" @click="getPortfolio()">Refresh
              </v-btn>
            </v-col>
            <v-col cols="8" class="d-flex justify-center align-center px-2 py-0">
              <ConfirmPurchase :selectedIndex="selectedIndex" :toPurchase="toPurchase"
                :targetSize="totalPortfolioSizeNumber" :cash="cash" :refreshCallback="getPortfolio" />
            </v-col>
          </v-card-actions>
          <v-card-text>
            <PortfolioView :searchQuery="searchQuery" :portfolio="portfolio" :targetSize="totalPortfolioSizeNumber" />
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols=6>
        <v-card>
          <v-card-title style="min-height: 90px;" class="text-center">
            <v-select @update:modelValue="newValue => getTargetPortfolio(newValue)" v-model="selectedIndex"
              :items="indexKeys" density="compact" variant="solo" label="Target Portfolio"></v-select>
          </v-card-title>
          <v-card-actions>
            <TailorComponent />
            <v-spacer />
            <IconTooltip
              text="Further customize the selected index by excluding or reweighting individual stocks or lists of stocks" />
          </v-card-actions>
          <v-card-text>
            <TargetPortfolioView v-if="targetPortfolio" :portfolio="targetPortfolio" :searchQuery="searchQuery"
              :targetSize="totalPortfolioSizeNumber" />
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
    <v-card-actions class="pa-6">
      <v-row>
        <v-col>
          <v-row v-if="targetPortfolio" justify="center">Showing up to {{ displayLength }} of {{ portfolio.holdings.length
          }} and {{ targetPortfolio.holdings.length }}</v-row>
          <v-row v-else justify="center">Showing up to {{ displayLength }} of {{ portfolio.holdings.length }}</v-row>
          <v-row justify="center"><v-btn @click="expandList()">Load More</v-btn></v-row>
        </v-col>
      </v-row>
    </v-card-actions>


  </v-card>
</template>
<style>
.input-field {
  height: 48px;
  /* Adjust the height value as needed */
}
</style>
<script>
//Vue
import { shallowRef } from 'vue';

//Components
import PortfolioView from "./PortfolioView.vue"
import TargetPortfolioView from "./TargetPortfolioView.vue"
import TailorComponent from './TailorComponent.vue';
import IconTooltip from './generic/IconTooltip.vue'
import ConfirmPurchase from './purchase/ConfirmPurchase.vue'

// Models
import PortfolioModel from '../models/PortfolioModel';
import PortfolioElementModel from '../models/PortfolioElementModel';
import TargetPortfolioModel from '../models/TargetPortfolioModel';
import TargetPortfolioElementModel from '../models/TargetPortfolioElementModel';

import CurrencyModel from '../models/CurrencyModel'

//API
import instance from '../api/instance'
import exceptions from '../api/exceptions'


import { mapActions } from 'vuex';

import {
  debounce
} from 'lodash';


// function parse_target_portfolio_model({
//   holdings,
//   source_date
// }) {
//   return new TargetPortfolioModel({
//     'holdings': holdings.map(holding => new TargetPortfolioElementModel(holding)),
//     'source_date': source_date
//   });
// }

export default {
  name: "App",
  components: {
    PortfolioView,
    TargetPortfolioView,
    TailorComponent,
    IconTooltip,
    ConfirmPurchase
  },
  data() {
    const portHoldings = shallowRef([])
    return {
      portfolio: new PortfolioModel(portHoldings),
      indexKeys: [],
      targetPortfolio: null,
      // targetPortfolios: new TargetPortfolioListModel({
      //   'loaded': initHoldings
      // }),
      portfolioTarget: 100_000,
      totalPortfolioSizeNumber: 100_000,
      toPurchase: 50,
      selectedIndex: null,
      compareLoading: false,
      refreshLoading: false,
      searchQueryInternal: '',
      searchQuery: '',
      cash: new CurrencyModel({
        value: 0,
        currency: '$'
      })
    };
  },
  computed: {

    loading() {
      return this.compareLoading || this.refreshLoading;
    },
    // totalPortfolioSizeNumber() {
    //   return Number(this.portfolioTarget);
    // },
    portfolioSum() {
      return this.portfolio.holdings.reduce((sum, holding) => sum + holding.value.value, 0);
    },
    portfolioPercentOfTarget() {
      return Math.round((this.portfolioSum / this.totalPortfolioSizeNumber) * 100);
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
    displayLength() {
      return this.$store.getters.displayLength
    }
  },
  methods: {
    ...mapActions(['setDisplayLength', 'setStockLists']),
    handlePortfolioSearchText: debounce(function () {
      // Code to execute after the debounce delay
      this.searchQuery = this.searchQueryInternal
    }, 300),
    handlePortfolioSizeInput: debounce(function () {
      // Code to execute after the debounce delay
      this.totalPortfolioSizeNumber = Number(this.portfolioTarget)
    }, 300), // Debounce delay in milliseconds
    // compareToIndex() {
    //   this.compareLoading = true;
    //   return instance.post('http://localhost:3000/compare_index', {
    //     'to_purchase': this.toPurchase,
    //     'index': this.selectedIndex
    //   }).then((response) => {
    //     console.log(response.data)
    //   }).finally(() => {
    //     this.compareLoading = false;
    //   });
    // },
    getTargetPortfolio(newValue) {
      const target = newValue || this.selectedIndex;
      return instance.post('http://localhost:3000/generate_index', {
        'index': target,
        'stock_exclusions': Array.from(this.$store.getters.excludedTickers),
        'list_exclusions': Array.from(this.$store.getters.excludedLists),
        'stock_modifications': this.$store.getters.stockModifications,
        'list_modifications': this.$store.getters.listModifications
      }).then((response) => {
        const portfolioHoldings = response.data.holdings.map(
          dict => new TargetPortfolioElementModel(dict));
        this.targetPortfolio = new TargetPortfolioModel({
          'holdings': portfolioHoldings,
          'source_date': response.data.source_date
        });
      });

    },
    getPortfolio() {
      this.refreshLoading = true;
      return instance.get('http://localhost:3000/portfolio').then((response) => {
        const portfolioHoldings = response.data.holdings.map(
          dict => new PortfolioElementModel(dict));
        this.portfolio.holdings = portfolioHoldings; //= new PortfolioModel(portfolioHoldings);
        if (response.data.cash) {
          this.cash = new CurrencyModel(response.data.cash);
        }
      }).catch(error => {
        if (error instanceof exceptions.auth) {
          // Handle the custom exception
          console.log('Authentication error, redirecting')
        } else {
          throw error
        }
      }).finally(() => {
        this.refreshLoading = false;
      })
    },
    getIndexes() {
      return instance.get('http://localhost:3000/indexes').then((response) => {
        this.indexKeys = response.data;
      });
    },
    getStockLists() {
      return instance.get('http://localhost:3000/stock_lists').then((response) => {
        this.setStockLists(response.data.loaded)
      });
    },

    buyIndex() {
      return instance.post('http://localhost:3000/buy_index', {
        'to_purchase': this.toPurchase,
        'index': this.selectedIndex
      }).then(() => {
        this.getPortfolio();
      });
    },
    expandList() {
      this.setDisplayLength(this.$store.getters.displayLength + 50)
    }
  },
  mounted() {
    this.getPortfolio()
    this.getIndexes()
    this.getStockLists()
    this.$store.watch(
      (_state, getters) => [
        getters.excludedTickers,
        getters.excludedLists,
        getters.stockModifications,
        getters.listModifications],
      () => {
        console.log('SOMETHING CHANGED')
        if (this.selectedIndex) {
          console.log('Updating target portfolio')
          this.getTargetPortfolio();
        }

      }
    );
  },
};
</script>
