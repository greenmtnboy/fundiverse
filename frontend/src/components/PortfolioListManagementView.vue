<template>
  <v-card>
    <v-card-title>Portfolio Management</v-card-title>
    <v-card-actions>
      <AddPortfolioPopup />
      <v-btn v-if="showSaveSuccess" transition="fade-transition">
        <v-icon>mdi-check</v-icon>
      </v-btn>
      <v-btn v-else transition="fade-transition" :loading="saving" @click="savePortfolios">
        Save Portfolios
      </v-btn>
      <v-btn v-if="showLoadSuccess" transition="fade-transition">
        <v-icon>mdi-check</v-icon>
      </v-btn>
      <v-btn v-else transition="fade-transition" :loading="saving" @click="loadPortfolios">
        Undo Changes
      </v-btn>
    </v-card-actions>
    <v-divider />
    <v-container>
      <v-row dense>
        <v-col cols=12 min-width="300px">
          <template v-if="portfolioLoadingStatus">
            <v-progress-linear height="10" indeterminate color="primary"></v-progress-linear>
          </template>
          <template v-for="portfolio in compositePortfolios" :key="portfolio.name">
            <CompositePortfolio :portfolio="portfolio" />
          </template>
        </v-col>
      </v-row>
    </v-container>

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

import CompositePortfolio from '@/components/portfolio/CompositePortfolio';
import AddPortfolioPopup from './portfolio/AddPortfolioPopup.vue';
import { mapGetters, mapActions } from 'vuex';

export default {
  name: "ManagePortfolioListView",
  components: {
    CompositePortfolio,
    AddPortfolioPopup
  },
  data() {
    return {
      indexKeys: [],
      portfolios: [],
      showSaveSuccess: false,
      showLoadSuccess: false,
      saving:false
    };
  },
  computed: {
    ...mapGetters(['compositePortfolios', 'portfolioLoadingStatus', 'provider']),
    // provider() {
    //   return this.$store.getters.provider;
    // },
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
    // ...mapActions(['refreshCompositePortfolios']),
    ...mapActions(['saveCompositePortfolios', 'loadCompositePortfolios']),
    async savePortfolios() {
      this.saving=true;
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
    async loadPortfolios() {
      this.saving = true;
      await this.loadCompositePortfolios();
      // Reset the success state after a delay
      setTimeout(() => {
        this.saving = false;
        this.showLoadSuccess = true;
      }, 1000);
      setTimeout(() => {
        this.showLoadSuccess = false;
      }, 2500);
      // await this.refreshCompositePortfolios();
      // this.refreshLoading = true;
      // return this.refreshCompositePortfolios.then(() => {
      // }).catch(error => {
      //   if (error instanceof exceptions.auth) {
      //     // Handle the custom exception
      //     console.log('Authentication error, redirecting')
      //   } else {
      //     throw error
      //   }
      // })
    },
  },
  async mounted() {
    await this.loadPortfolios();
  },
};
</script>
  