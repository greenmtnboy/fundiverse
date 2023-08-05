<template>
  <v-card>
    <v-card-title class="d-flex justify-center align-center">Configure {{ portfolioName }}</v-card-title>
    <v-row class="d-flex justify-center align-center px-2">
      <v-col cols="6">
        <v-text-field class="input-field" variant="solo" @input="handlePortfolioSizeInput" label="Target Portfolio Size"
          v-model="portfolioTarget" :rules="numberValidationRules">
        </v-text-field>
      </v-col>
      <v-col cols="6">
        <v-text-field @update:modelValue="newValue => handlePortfolioSearchText(newValue)" class="input-field"
          label="Search Tickers" variant="solo" v-model="searchQueryInternal" placeholder="AAPL" /></v-col>
    </v-row>
    <v-row class="min-display">
      <v-col cols=6 min-width="300px">
        <v-card>
          <v-card-title style="min-height: 90px;" class="text-center">
            <v-select v-model="selectedSubPortfolio" :items="subPortfolioKeys" density="compact" variant="solo"
              label="Sub Portfolio" :disabled="compareLoading"></v-select>
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
              <v-btn color="primary" :loading="refreshLoading" class="d-flex flex-column" @click="saveChanges()">Save
                Changes
              </v-btn>

            </v-col>
          </v-card-actions>
          <v-card-text>
            <PortfolioView :searchQuery="searchQuery" :portfolio="displayPortfolio" :targetSize="portfolio.target_size" />
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
            <TailorComponent :portfolioName="portfolioName" />
            <IconTooltip
              text="Further customize the selected index by excluding or reweighting individual stocks or lists of stocks" />
            <v-checkbox-btn :disabled="!selectedIndex" v-model="reweightTarget"
              @update:modelValue="newValue => getTargetPortfolio(selectedIndex)" label="Reweight" />
            <IconTooltip
              text="Scale the weights of stocks in the index by the changes in their prices from the date of the index (ex Q3 20203)" />
            <v-spacer />
          </v-card-actions>

          <v-card-text>
            <v-row class="py-5" height="15" v-if="targetLoading">
              <v-progress-linear height="10" indeterminate color="primary"></v-progress-linear>

            </v-row>
            <TargetPortfolioView v-else-if="targetPortfolio" :portfolio="targetPortfolio" :searchQuery="searchQuery"
              :targetSize="portfolio.target_size" />
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

// Models
import TargetPortfolioModel from '../models/TargetPortfolioModel';
import TargetPortfolioElementModel from '../models/TargetPortfolioElementModel';
import CurrencyModel from '../models/CurrencyModel'
import CompositePortfolioModel from "@/models/CompositePortfolioModel";

//API
import instance from '../api/instance'
import exceptions from '../api/exceptions'

import { mapActions, mapGetters } from 'vuex';

import { debounce } from 'lodash';


export default {
  name: "CompositePortfolioManagementView",
  components: {
    PortfolioView,
    TargetPortfolioView,
    TailorComponent,
    IconTooltip,
    // ConfirmPurchase
  },
  props: {
    portfolioName: {
      type: String,
      required: false,
      default: ''
    }
  },
  data() {
    return {
      indexKeys: [],
      targetPortfolio: null,
      // targetPortfolios: new TargetPortfolioListModel({
      //   'loaded': initHoldings
      // }),
      portfolioTarget: null,
      reweightTarget: false,
      selectedIndex: null,
      targetLoading: false,
      compareLoading: false,
      refreshLoading: false,
      searchQueryInternal: '',
      searchQuery: '',
      selectedSubPortfolio: 'All',
      saving: false,
      showSaveSuccess: false,
      cash: new CurrencyModel({
        value: 0,
        currency: '$'
      })
    };
  },
  computed: {
    ...mapGetters(['compositePortfolios', 'portfolioCustomizations']),
    routerDebug() {
      return this.$route.params;
    },
    subPortfolioKeys() {
      const keys = [...this.portfolio.keys];
      keys.push('All')
      return keys

    },
    displayPortfolio() {
      const local = this;
      if (this.selectedSubPortfolio === 'All') {
        return this.portfolio
      }
      else {
        return this.portfolio.components.find((portfolio) => portfolio.provider === local.selectedSubPortfolio)
      }
    },
    portfolioCustomization() {
      const customization = this.portfolioCustomizations.get(this.portfolio.name)
      return customization
    },
    portfolio() {
      const matched = this.compositePortfolios.find((portfolio) => portfolio.name === this.portfolioName)

      if (!matched) {
        return new CompositePortfolioModel({
          name: this.portfolioName, holdings: [],
          components: [], cash: { value: 0, currency: '$' }
        })
      }
      return matched
    },
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
    ...mapActions(['setDisplayLength', 'setStockLists', 'loadDefaultModifications', 'loadCompositePortfolios',
      'saveCompositePortfolios', 'saveCustomizations', 'loadCustomizations', 'getStockLists',
      'setPortfolioSize']),
    handlePortfolioSearchText: debounce(function () {
      // Code to execute after the debounce delay
      this.searchQuery = this.searchQueryInternal
    }, 300),
    handlePortfolioSizeInput: debounce(function () {
      // Code to execute after the debounce delay
      this.setPortfolioSize({ portfolioName: this.portfolioName, size: Number(this.portfolioTarget) })
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
      return instance.post('generate_index', {
        'provider': this.provider,
        'index': target,
        'stock_exclusions': Array.from(this.portfolioCustomization.excludedTickers),
        'list_exclusions': Array.from(this.portfolioCustomization.excludedLists),
        'stock_modifications': this.portfolioCustomization.stockModifications,
        'list_modifications': this.portfolioCustomization.listModifications,
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
      // shim in current getter
      // TODO: clean up later
      if (!this.portfolioTarget) {
        this.portfolioTarget = this.portfolio.target_size
      }
      if (!this.selectedIndex && this.portfolioCustomization) {
        this.selectedIndex = this.portfolioCustomization.indexPortfolio;
        this.reweightTarget = this.portfolioCustomization.reweightTarget;
        this.getTargetPortfolio()

      }
      return this.compositePortfolios
    },
    async saveChanges() {
      this.saving = true;
      await this.saveCompositePortfolios();
      // Reset the success state after a delay
      setTimeout(() => {
        this.saving = false;
        this.showSaveSuccess = true;
      }, 1000);
      setTimeout(() => {
        this.showSaveSuccess = false;
      }, 2500);
    },
    getIndexes() {
      return instance.get('indexes').then((response) => {
        this.indexKeys = response.data;
      });
    },
    buyIndex() {
      return instance.post('buy_index', {
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
  async mounted() {
    await this.loadCustomizations();
    await this.loadCompositePortfolios();
    await this.getPortfolio()

    // this.getPortfolio()
    this.getIndexes()

    this.getStockLists()
    // this.loadDefaultModifications()
    this.$store.watch(
      (_state, getters) => [
        getters.portfolioCustomizations],
      () => {
        if (this.selectedIndex) {
          this.getTargetPortfolio();
        }

      }
    );
  },
};
</script>
  