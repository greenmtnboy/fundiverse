<template>
  <v-list class="pt-0" density="compact" v-if="portfolio.holdings.length > 0">
    <template v-for="element in shortList" :key="element.ticker">
      <TargetPortfolioElement
        :element="element"
        :totalPortfolioSize="targetSize"
        :portfolioName="portfolioName"
      />
    </template>
  </v-list>
</template>

<script lang="ts">
import TargetPortfolioElement from "./TargetPortfolioElement.vue";
import TargetPortfolioModel from "../../models/TargetPortfolioModel";

export default {
  name: "TargetPortfolioView",
  components: {
    TargetPortfolioElement,
  },
  props: {
    portfolio: {
      type: TargetPortfolioModel,
      required: true,
    },
    portfolioName: {
      type: String,
      required: false,
    },
    targetSize: {
      type: Number,
      required: false,
    },
    searchQuery: {
      type: String,
      required: false,
      default: "",
    },
  },
  computed: {
    shortList() {
      const query = this.searchQuery.toLowerCase();
      const filtered = this.portfolio.holdings.filter((item) =>
        item.ticker.toLowerCase().includes(query),
      );

      const shortenedList = filtered.slice(
        0,
        this.$store.getters.displayLength,
      );
      return shortenedList;
    },
  },
};
</script>
