<template>
    <v-card
      :title="`Target (${portfolio.holdings.length})`"
      class="sharp"
    >
      <v-list class="pt-0" density="compact" v-if="portfolio.holdings.length > 0">
        <template v-for="element in shortList" :key="element.ticker">
          <TargetPortfolioElement
            :element="element"
            :totalPortfolioSize="targetSize"
          />
        </template>
      </v-list>
      <v-card-actions
        ><v-btn @click="displayLength = displayLength + 10"
          >See more</v-btn
        ></v-card-actions
      >
    </v-card>
  </template>
  <style>
  .sharp {
    border-radius: 0;
  }
  </style>
  
  <script lang="ts">
  import TargetPortfolioElement from "./TargetPortfolioElement.vue";
  import TargetPortfolioModel from "../models/TargetPortfolioModel";
  
  export default {
    name: "TargetPortfolioView",
    components: {
      TargetPortfolioElement,
    },
    data() {
      return {
        displayLength: 50,
      };
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
        const shortenedList = filtered.slice(0, this.displayLength);
        return shortenedList;
      },
    },
  };
  </script>
  