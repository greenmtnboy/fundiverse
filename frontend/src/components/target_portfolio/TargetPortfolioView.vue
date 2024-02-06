<template>
  <v-list class="pt-0" density="compact" v-if="portfolio.holdings.length > 0">
    <!-- <v-pagination
      v-model="portfolio.holdings"
      :total-items="portfolio.holdings.length"
      :items-per-page="itemsPerPage"
      prev-icon="mdi-chevron-left"
      next-icon="mdi-chevron-right"
      :disabled="loading"
    >    <template v-slot:default="{ item }">
        <TargetPortfolioElement :element="item" :totalPortfolioSize="targetSize" />
    </template></v-pagination>
   -->
    <!-- <v-virtual-scroll
  :items="portfolio.holdings"
  height="320"
      item-height="48"
>
    <template v-slot:default="{ item }">
        <TargetPortfolioElement :element="item" :totalPortfolioSize="targetSize" />
    </template>
</v-virtual-scroll> -->

    <template v-for="element in shortList" :key="element.ticker">
      <TargetPortfolioElement
        :element="element"
        :totalPortfolioSize="targetSize"
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
