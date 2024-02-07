<template>
  <v-list-item>
    <template v-slot:prepend>
      <ProviderIcon :iconType="portfolio.provider" />
    </template>
    <v-list-item-title>{{ portfolio.name }}</v-list-item-title>
    <span>
      <CurrencyItem
        :loading="portfolio.loading"
        :value="{ currency: '$', value: portfolioSum }"
      />
      in {{ portfolioLength }} stocks
    </span>
    <v-spacer></v-spacer>
    <span class="text-medium-emphasis">
      <CurrencyItem :loading="portfolio.loading" :value="portfolio.cash" /> cash
    </span>
    <template v-slot:append>
      <v-chip
        v-if="portfolio.profit_or_loss"
        :color="portfolioColor"
        small
        outlined
      >
        <span class="pr-2">Return: </span>
        <CurrencyItem :value="portfolio.profit_or_loss" />
      </v-chip>
      <v-spacer />
      <ProviderLoginPopup
        stateful
        :provider="portfolio.provider"
        :portfolioName="parentName"
      ></ProviderLoginPopup>
      <!-- <v-btn v-if="loggedIn" color="green" icon="mdi-check" variant="text"></v-btn> -->
      <!-- <v-btn v-else color="grey-lighten-1" icon="mdi-login" variant="text"></v-btn> -->
      <v-spacer />
      <v-btn
        v-if="loggedIn"
        @click="removeProvider"
        color="red"
        prependIcon="mdi-cancel"
        variant="text"
      >
        Remove
      </v-btn>
      <!-- <v-btn :loading="loading" v-if="refresh" @click="refresh" color="blue" prependIcon="mdi-refresh" variant="text">
                Refresh
            </v-btn> -->
    </template>
  </v-list-item>
</template>

<script lang="ts">
import CurrencyItem from "../generic/CurrencyItem.vue";
import ProviderIcon from "../icons/ProviderIcon.vue";
import ProviderLoginPopup from "/src/components/portfolio/ProviderLoginPopup.vue";
import SubPortfolioModel from "/src/models/SubPortfolioModel";
export default {
  data() {
    return {
      loggedIn: true,
      selfLoading: false,
    };
  },
  components: {
    CurrencyItem: CurrencyItem,
    ProviderIcon: ProviderIcon,
    ProviderLoginPopup: ProviderLoginPopup,
  },
  methods: {
    removeProvider() {
      this.$store.dispatch("removeProvider", {
        portfolioName: this.parentName,
        provider: this.portfolio.provider,
      });
    },
  },
  props: {
    parentName: {
      type: String,
      required: false,
      default: "",
    },
    portfolio: {
      type: SubPortfolioModel,
      required: true,
    },
    refresh: {
      type: Function,
      required: false,
      default: () => {},
    },
  },
  computed: {
    loading() {
      return this.portfolio.loading;
    },
    portfolioSum() {
      return (
        this.portfolio.holdings.reduce(
          (sum, holding) =>
            (sum + Math.floor(holding.value.value * 10000)) >>> 0,
          0,
        ) / 10000
      );
    },
    portfolioLength() {
      return this.portfolio.holdings.length;
    },
    portfolioColor() {
      if (this.portfolio.profit_or_loss.value > 0) {
        return "green";
      } else if (this.portfolio.profit_or_loss.value < 0) {
        return "red";
      }
      return "gray";
    },
  },
};
</script>
