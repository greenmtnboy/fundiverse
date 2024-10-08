<template>
  <v-list-item>
    <div>
      <TickerDisplay :ticker="element.ticker" />
      <p class="text-medium-emphasis">
        <CurrencyItem :value="elementValue"></CurrencyItem> ({{
          elementWeight
        }}%)
      </p>
    </div>
    <template v-slot:append>
      <v-tooltip v-if="portfolioName">
        <template v-slot:activator="{ props }">
          <v-btn
            :disabled="excluded"
            v-bind="props"
            @click="onClickWrapper"
            icon
            density="compact"
          >
            <v-icon :loading="loading" color="warning">mdi-cancel</v-icon>
          </v-btn>
        </template>
        <span>Exclude</span>
      </v-tooltip>
    </template>
  </v-list-item>
</template>

<script lang="ts">
import TargetPortfolioElementModel from "../../models/TargetPortfolioElementModel";
import TickerDisplay from "../generic/TickerDisplay.vue";
import CurrencyItem from "../generic/CurrencyItem.vue";
import { mapActions } from "vuex";

export default {
  name: "TargetPortfolioElement",
  data() {
    return {
      loading: false,
      excluded: false,
    };
  },
  components: { TickerDisplay, CurrencyItem },
  methods: {
    ...mapActions(["excludeStock"]),
    onClickWrapper() {
      this.loading = true;
      this.excluded = true;
      this.excludeStock({ticker:this.element.ticker, portfolio:this.portfolioName}).finally(() => {
        this.loading = false;
      });
      // if (this.onClick) {
      //   this.onClick(this.element).then(() => { }).finally(() => {
      //     this.loading = false
      //     this.store
      //   });
      // } else {
      //   this.loading = false;
      // }
    },
  },
  props: {
    element: {
      type: TargetPortfolioElementModel,
      required: true,
    },
    totalPortfolioSize: {
      type: Number,
      required: false,
    },
    portfolioName: {
      type: String,
      required: false,
    },
    onClick: {
      type: Function,
      required: false,
    },
  },
  computed: {
    elementWeight() {
      return Math.round(this.element.weight * 10000) / 100;
    },
    elementValue() {
      return {
        value: Math.round(this.totalPortfolioSize * this.element.weight),
        currency: "$",
      };
    },
  },
};
</script>
