<template>
  <v-card class="ma-4">
    <v-card-title :data-testid="`cmp-port-${portfolio.name}`" :key="portfolio.name" style="display:'flex'">
      <v-row>
        <v-col col="8">
          {{ portfolio.name }}
          <span class="text-low-emphasis" style="opacity:0.5; font-size: small">({{ timeDisplay }})</span>
        </v-col><v-col class="text-right" col="4">
          <span>
            <v-tooltip>
              <template v-slot:activator="{ props }">
                <v-chip v-if="portfolio.profit_or_loss" v-bind="props" :color="portfolioColor" small outlined>
                  <span class="pr-2">Portfolio Return: </span>
                  <CurrencyItem
                    :value="portfolio.profit_or_loss.value ? portfolio.profit_or_loss : { currency: 'USD', value: portfolio.profit_or_loss }" />
                </v-chip>
              </template>
              <span>Dividends:
                <CurrencyItem v-if="portfolio.dividends" :value="portfolio.dividends" /> Appreciation:
                <CurrencyItem v-if="portfolio.appreciation" :value="portfolio.appreciation" />
              </span>
            </v-tooltip>
          </span></v-col>
      </v-row>
    </v-card-title>
    <v-alert type="error" v-if="portfolio.error">{{ portfolio.error }}</v-alert>
    <v-card-text class="text-high-emphasis text--primary">
      <div>
        <p class="text-high-emphasis font-weight-black text--primary">
          A portfolio across {{ portfolio.components.length }} providers with
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

      <template v-for="sportfolio in portfolio.components" :key="sportfolio.name">
        <SubPortfolio :id="sportfolio.name" :portfolio="sportfolio" :parentName="portfolio.name"
          :refresh="() => refreshChild(sportfolio)" />
      </template>
      <!-- <div v-for="sportfolio in portfolio.components" :key="sportfolio.name"> 
                {{ sportfolio.holdings }}</div> -->
      <v-alert type="info" v-if="portfolio.keys.length === 0" closable close-label="Dismiss Hint">Add a provider to get
        started! Providers are the actual brokerages that
        can hold your stocks and are needed to fetch up-to-date stock
        information as you set up your portfolio. If you're just getting
        started, you can sign up for a Alpaca paper account in minutes and
        explore with fake money, no bank account provided.
      </v-alert>
      <v-alert type="info" v-if="!selectedIndex" closable close-label="Dismiss Hint">Click the configure button to set
        up an
        index to build against for this
        portfolio. You can choose from a variety of pre-built indexes, or build
        your own! You'll need an index set to start purchasing stocks.
      </v-alert>
    </v-card-text>
    <v-card-actions>
      <ConfirmPurchase :selectedIndex="selectedIndex" :targetSize="portfolio.target_size" :cash="portfolio.cash"
        :providers="portfolio.keys" :portfolioName="portfolio.name" :disabled="portfolio.loading" />
      <v-btn :disabled="portfolio.keys.length === 0" @click="navigatePortfolio">
        Configure
      </v-btn>
      <ProviderLoginPopup  :portfolioName="portfolio.name" :providerKeys="portfolio.keys" />

      <v-btn :disabled="portfolio.keys.length === 0 || portfolio.loading" @click="refresh">
        Refresh
      </v-btn>
      <ConfirmationButton :dataTestId="`btn-del-${portfolio.name}`" :onClick="remove" text="Delete" />
      <!-- <v-btn :disabled="portfolio.loading" @click="remove"  color="red" prependIcon="mdi-cancel">
                Delete
            </v-btn> -->
    </v-card-actions>
  </v-card>
</template>

<script lang="ts">
import CompositePortfolioModel from "/src/models/CompositePortfolioModel";
import ProviderLoginPopup from "/src/components/portfolio/ProviderLoginPopup.vue";
import SubPortfolio from "./SubPortfolio.vue";
import CurrencyItem from "../generic/CurrencyItem.vue";
import ConfirmPurchase from "../purchase/ConfirmPurchase.vue";
import ConfirmationButton from "../generic/ConfirmationButton.vue";
import { mapActions, mapGetters } from "vuex";
export default {
  name: "CompositePortfolioView",
  components: {
    SubPortfolio,
    ProviderLoginPopup,
    CurrencyItem,
    ConfirmPurchase,
    ConfirmationButton,
  },
  data() {
    return {
      saving: false,
      showSaveSuccess: false,
      showLoadSuccess: false,
    };
  },
  computed: {
    ...mapGetters(["portfolioCustomizations", "indexes"]),
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
      const custom = this.portfolioCustomizations.get(this.portfolio.name);
      return custom;
    },
    customizationCount() {
      if (this.customizations) {
        return this.customizations.customizationCount;
      }
      return 0;
    },
    portfolioColor() {
      if (this.portfolio.profit_or_loss.value > 0) {
        return "green";
      } else if (this.portfolio.profit_or_loss.value < 0) {
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
      "refreshCompositePortfolio",
      "saveCompositePortfolios",
      "removeCompositePortfolio",
    ]),
    navigatePortfolio() {
      this.$router.push({ path: `composite_portfolio/${this.portfolio.name}` });
    },
    async refreshChild(sportfolio) {
      await this.refreshCompositePortfolio({
        portfolioName: this.portfolio.name,
        keys: this.portfolio.keys,
        keys_to_refresh: [sportfolio.provider],
      });
      await this.saveCompositePortfolios();
    },
    async refresh() {
      this.error = null;
      try {
        await this.refreshCompositePortfolio({
          portfolioName: this.portfolio.name,
          keys: this.portfolio.keys,
          keys_to_refresh: this.portfolio.keys,
        });
        await this.saveCompositePortfolios();
      } catch (e) {
        this.error = e;
      }
    },
    async remove() {
      await this.removeCompositePortfolio({
        portfolioName: this.portfolio.name,
        keys: this.portfolio.keys,
      });
    },
  },
};
</script>
