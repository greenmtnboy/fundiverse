<template>
  <v-card>
    <v-card-title class="d-flex justify-center align-center">Portfolio List</v-card-title>
    <v-container>
      <v-row dense>
      <v-col cols=12 min-width="300px">
        <template v-for="portfolio in portfolios" :key="portfolio.name" >
          <CompositePortfolio :portfolio="portfolio" />
        </template>
      </v-col>
    </v-row>
    </v-container>
    <v-card-actions>
      <v-btn variant="outlined">
        New Portfolio
      </v-btn>
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
//API
import instance from '../api/instance'
import exceptions from '../api/exceptions'

import CompositePortfolioModel from '@/models/CompositePortfolioModel';
import CompositePortfolio from '@/components/portfolio/CompositePortfolio';

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
  name: "ManagePortfolioListView",
  components: {
    CompositePortfolio
  },
  data() {
    return {
      indexKeys: [],
      refreshLoading: false,
      portfolios: []
    };
  },
  computed: {

    loading() {
      return this.compareLoading || this.refreshLoading;
    },
    provider() {
      return this.$store.getters.provider;
    },
    // portfolioSum() {
    //   return 0.0
    //   // return this.portfolio.holdings.reduce((sum, holding) => sum + holding.value.value, 0);
    // },
    // portfolioPercentOfTarget() {
    //   return Math.round((this.portfolioSum / this.totalPortfolioSizeNumber) * 100);
    // },
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
    getPortfolios() {
      this.refreshLoading = true;
      return instance.get(`http://localhost:3000/composite_portfolios`).then((response) => {
        this.portfolios = response.data.map(dict => new CompositePortfolioModel(dict));
        // const portfolioHoldings = response.data.holdings.map(
        //   dict => new PortfolioElementModel(dict));
        // this.portfolio.holdings = portfolioHoldings; //= new PortfolioModel(portfolioHoldings);
        // if (response.data.cash) {
        //   this.cash = new CurrencyModel(response.data.cash);
        // }
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
  },
  mounted() {
    this.getPortfolios();
  },
};
</script>
  