<template>
  <v-card>
    <v-card-title class="d-flex justify-center align-center">Portfolio Management</v-card-title>
    <v-row class="d-flex justify-center align-center px-2">
      <v-col cols="6">
        <v-text-field class="input-field" variant="solo" @input="handlePortfolioSizeInput" label="Target Portfolio Size"
          v-model="portfolioTarget" :rules="numberValidationRules">
        </v-text-field>
      </v-col>
      <v-col cols="6">
        <v-text-field @update:modelValue="newValue => handlePortfolioSearchText(newValue)" class="input-field"
          label="Filter Tickers" variant="solo" v-model="searchQueryInternal" placeholder="AAPL" /></v-col>
    </v-row>
    <v-row class="min-display">
      <v-col cols=6 min-width="300px">
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
              <ConfirmPurchase :selectedIndex="selectedIndex" :targetSize="totalPortfolioSizeNumber" :cash="cash"
                :refreshCallback="getPortfolio" />
            </v-col>
          </v-card-actions>
          <v-card-text>
            <PortfolioView :searchQuery="searchQuery" :portfolio="portfolio" :targetSize="totalPortfolioSizeNumber" />
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols=6 min-width="300px">
        <v-card>
          <v-card-title style="min-height: 90px;" class="text-center">
            <v-select @update:modelValue="newValue => getTargetPortfolio(newValue)" v-model="selectedIndex"
              :items="indexKeys" density="compact" variant="solo" label="Target Portfolio"
              :disabled="compareLoading"></v-select>
          </v-card-title>
          <v-card-actions>
            <TailorComponent />
            <IconTooltip
              text="Further customize the selected index by excluding or reweighting individual stocks or lists of stocks" />

            <!-- <v-spacer /> -->
            <v-checkbox-btn v-model="reweightTarget" @update:modelValue="newValue => getTargetPortfolio(selectedIndex)"
              label="Reweight" />
            <IconTooltip
              text="Scale the weights of stocks in the index by the changes in their prices from the date of the index (ex Q3 20203)" />
            <v-spacer />
          </v-card-actions>

          <v-card-text>
            <v-row class="py-5" height="15" v-if="targetLoading">
              <v-progress-linear height="10" indeterminate color="primary"></v-progress-linear>

            </v-row>
            <TargetPortfolioView v-else-if="targetPortfolio" :portfolio="targetPortfolio" :searchQuery="searchQuery"
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
          <v-row justify="center"><v-btn v-if="maxLength > displayLength" @click="expandList()">Load More</v-btn></v-row>
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

.custom-card {
  min-width: 600px;
  /* Adjust the value as per your requirement */
}
</style>
<script>

//Components
import PortfolioView from "./portfolio/PortfolioView.vue"
import TargetPortfolioView from "./target_portfolio/TargetPortfolioView.vue"
import TailorComponent from './tailor/TailorComponent.vue';
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
    return {
      portfolio: new PortfolioModel([]),
      indexKeys: [],
      targetPortfolio: null,
      // targetPortfolios: new TargetPortfolioListModel({
      //   'loaded': initHoldings
      // }),
      portfolioTarget: 100_000,
      totalPortfolioSizeNumber: 100_000,
      reweightTarget: false,
      selectedIndex: null,
      targetLoading: false,
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
    provider() {
      return this.$store.getters.provider;
    },
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
    },
    maxLength() {
      if (!this.targetPortfolio) {
        return this.portfolio.holdings.length
      }
      return Math.max(this.portfolio.holdings.length, this.targetPortfolio.holdings.length)
    }
  },
  methods: {
    ...mapActions(['setDisplayLength', 'setStockLists', 'loadDefaultModifications']),
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
      this.targetLoading = true;
      const target = newValue || this.selectedIndex;
      return instance.post('http://localhost:3000/generate_index', {
        'provider': this.provider,
        'index': target,
        'stock_exclusions': Array.from(this.$store.getters.excludedTickers),
        'list_exclusions': Array.from(this.$store.getters.excludedLists),
        'stock_modifications': this.$store.getters.stockModifications,
        'list_modifications': this.$store.getters.listModifications,
        'reweight': this.reweightTarget
      }).then((response) => {
        const portfolioHoldings = response.data.holdings.map(
          dict => new TargetPortfolioElementModel(dict));
        this.targetPortfolio = new TargetPortfolioModel({
          'holdings': portfolioHoldings,
          'source_date': response.data.source_date
        });
        this.updatedPortfolioWithTargets();

      }).catch(error => {
        if (error instanceof exceptions.auth) {
          // Handle the custom exception
          console.log('Authentication error, redirecting')
        } else {
          throw error
        }
      }).finally(() => {
        this.targetLoading = false;
      });

    },
    updatedPortfolioWithTargets() {
      // update our existing portfolio with targets
      let newHoldings = [];
      this.portfolio.holdings.forEach((element) => {
        const targetElement = this.targetPortfolio.holdings.find((target) => target.ticker === element.ticker);
        if (targetElement) {
          element.targetWeight = targetElement.weight
        }
        newHoldings.push(element);
      });
      this.portfolio.holdings = newHoldings;
    },
    getPortfolio() {
      this.refreshLoading = true;
      return instance.get(`http://localhost:3000/portfolio/${this.provider}`).then((response) => {
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
      let next = Math.min(this.maxLength, this.$store.getters.displayLength + 50);
      this.setDisplayLength(next)
    }
  },
  mounted() {
    this.getPortfolio()
    this.getIndexes()
    this.getStockLists()
    this.loadDefaultModifications()
    this.$store.watch(
      (_state, getters) => [
        getters.excludedTickers,
        getters.excludedLists,
        getters.stockModifications,
        getters.listModifications],
      () => {
        if (this.selectedIndex) {
          this.getTargetPortfolio();
        }

      }
    );
  },
};
</script>
