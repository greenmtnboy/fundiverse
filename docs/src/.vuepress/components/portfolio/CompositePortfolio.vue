<template>
  <v-card  class="sharp mt-10">
    <v-card-title :data-testid="`cmp-port-${portfolio.name}`" :key="portfolio.name" style="display:'flex'">
      <v-row>
        <v-col col="8">
          {{ portfolio.name }}
          <span class="text-low-emphasis" style="opacity:0.5; font-size: small">({{ timeDisplay }})</span>
        </v-col>
        <v-col class="text-right" col="4">
          <span>
            <v-chip v-if="portfolio.profit_and_loss" :color="portfolioColor" small outlined>
              <span class="pr-2">Portfolio Return: </span>
              <CurrencyItem :value="portfolio.profit_and_loss" />
            </v-chip></span></v-col>
      </v-row>
    </v-card-title>
    <v-alert type="error" v-if="portfolio.error">{{ portfolio.error }}</v-alert>
    <v-card-text class="text-high-emphasis text--primary">
      <div>
        <p class="text-high-emphasis font-weight-black text--primary">
          A portfolio across {{ portfolio.components.length }} provider(s) with
          target size
          <CurrencyItem :value="{ currency: '$', value: portfolio.target_size }" />
        </p>
        <p v-if="selectedIndex">
          Based on index
          <span class="font-weight-black" :style="{ color: 'purple' }">{{
      this.selectedIndex
    }}</span>
          with {{ customizationCount }} customizations.
        </p>
        <p v-else :style="{ color: 'orange' }">
          No target index selected. Click customize to set.
        </p>
      </div>
      <div></div>
      <v-divider class="pb-4"></v-divider>
      <template v-if="portfolio.loading">
        <v-progress-linear indeterminate color="green-lighten-3" height="20">
        </v-progress-linear>
        <v-progress-linear indeterminate reverse color="blue-lighten-3" height="20">
        </v-progress-linear>
      </template>
      <template v-else>
        <v-progress-linear color="green-lighten-3" v-model="portfolioInTargetPercent" height="20">
          <p class="text-high-emphasis font-weight-black">
            <CurrencyItem :loading="portfolio.loading" :value="{ currency: '$', value: portfolioInTargetSum }" />, {{
      portfolioInTargetPercent }}% of target with index stocks
          </p>
        </v-progress-linear>
        <v-progress-linear color="blue-lighten-3" v-model="portfolioPercentOfTarget" height="20">
          <p class="text-high-emphasis font-weight-black">
            <CurrencyItem :loading="portfolio.loading" :value="{ currency: '$', value: portfolioSum }" />, {{
            portfolioPercentOfTarget }}% of target including all stocks
          </p>
        </v-progress-linear>
      </template>
    </v-card-text>
    <v-card-text class="pt-0">
      <v-divider class="pb-4 pt-0"></v-divider>
    </v-card-text>
  </v-card>
</template>

<script lang="ts">
import CompositePortfolioModel from "../models/CompositePortfolioModel";
import CurrencyItem from "../generic/CurrencyItem.vue";
import { mapActions, mapGetters } from "vuex";
export default {
  name: "CompositePortfolioView",
  components: {
    CurrencyItem,
  },
  data() {
    return {
      saving: false,
      showSaveSuccess: false,
      showLoadSuccess: false,
    };
  },
  computed: {
    ...mapGetters(["staticCustomization", "indexes"]),
    // TODO: disable buy button when not logged in
    // canPurchase() {
    //     for x in this.portfolio.components {
    //         if (x.holdings.length == 0) {
    //             return false
    //         }
    //     }
    // },
    timeDisplay() {
      const options: Intl.DateTimeFormatOptions = {
        weekday: "long",
        year: "numeric",
        month: "long",
        day: "numeric",
        hour: "numeric",
        minute: "numeric",
      };
      const dateString = new Date(
        this.portfolio.refreshed_at * 1000,
      ).toLocaleDateString(undefined, options);
      if (this.portfolio.error) {
        return `Refresh failed. Showing data as of ${dateString}.`;
      }
      return `Refreshed ${dateString}`;
    },
    customizations() {
      return this.staticCustomization;
    },
    customizationCount() {
      if (this.customizations) {
        return this.customizations.customizationCount;
      }
      return 0;
    },
    portfolioColor() {
      if (this.portfolio.profit_and_loss.value > 0) {
        return "green";
      } else if (this.portfolio.profit_and_loss.value < 0) {
        return "red";
      }
      return "gray";
    },
    selectedIndex() {
      if (!this.customizations) {
        return null;
      }
      return this.customizations.indexPortfolio;
    },
    portfolioMatchedHoldings() {
      const index = this.indexes.find(
        (element) => element.name == this.selectedIndex,
      );
      if (!index) {
        return [];
      }
      const indexTickers = index.holdings.reduce(
        (set, holding) => set.add(holding.ticker),
        new Set(),
      );
      return this.portfolio.holdings.filter((element) =>
        indexTickers.has(element.ticker),
      );
    },
    portfolioInTargetSum() {
      return Number(
        this.portfolioMatchedHoldings.reduce(
          (sum, holding) =>
            BigInt(sum + BigInt(Math.floor(holding.value.value * 10000))) >>
            BigInt(0),
          BigInt(0),
        ) / BigInt(10000),
      );
    },
    portfolioInTargetPercent() {
      return Math.round(
        (this.portfolioInTargetSum / this.portfolio.target_size) * 100,
      );
    },
    portfolioSum() {
      return Number(
        this.portfolio.holdings.reduce(
          (sum, holding) =>
            BigInt(sum + BigInt(Math.floor(holding.value.value * 10000))) >>
            BigInt(0),
          BigInt(0),
        ) / BigInt(10000),
      );
    },
    portfolioPercentOfTarget() {
      return Math.round((this.portfolioSum / this.portfolio.target_size) * 100);
    },

    // selectedIndex() {
    //     return this.$store.getters.selectedIndex;
    // }
  },
  props: {
    portfolio: {
      type: CompositePortfolioModel,
      required: true,
    },
  },
  methods: {
    ...mapActions([
    ]),




  },
};
</script>
