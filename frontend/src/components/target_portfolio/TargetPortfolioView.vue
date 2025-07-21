<template>
  <div>
    <!-- Sort Control Toggle -->
    <div class="sort-control mb-3">
      <v-btn
        :variant="sortOrder === 'desc' ? 'flat' : 'outlined'"
        :color="sortOrder === 'desc' ? 'primary' : 'default'"
        size="small"
        class="sort-btn"
        @click="setSortOrder('desc')"
      >
        High → Low
      </v-btn>
      <v-btn
        :variant="sortOrder === 'asc' ? 'flat' : 'outlined'"
        :color="sortOrder === 'asc' ? 'primary' : 'default'"
        size="small"
        class="sort-btn"
        @click="setSortOrder('asc')"
      >
        Low → High
      </v-btn>
    </div>

    <!-- Portfolio List -->
    <v-list class="pt-0" density="compact" v-if="portfolio.holdings.length > 0">
      <template v-for="element in shortList" :key="element.ticker">
        <TargetPortfolioElement
          :element="element"
          :totalPortfolioSize="targetSize"
          :portfolioName="portfolioName"
        />
      </template>
    </v-list>
  </div>
</template>

<style>
.sort-control {
  display: flex;
  gap: 2px;
  align-items: center;
}

.sort-btn {
  border-radius: 20px !important;
  text-transform: none;
  font-size: 12px;
  height: 28px;
  min-width: 80px;
  transition: all 0.2s ease;
}

.sort-btn:first-child {
  border-top-right-radius: 4px !important;
  border-bottom-right-radius: 4px !important;
}

.sort-btn:last-child {
  border-top-left-radius: 4px !important;
  border-bottom-left-radius: 4px !important;
}
</style>

<script lang="ts">
import TargetPortfolioElement from "./TargetPortfolioElement.vue";
import TargetPortfolioModel from "../../models/TargetPortfolioModel";

export default {
  name: "TargetPortfolioView",
  components: {
    TargetPortfolioElement,
  },
  data() {
    return {
      sortOrder: 'desc' as 'asc' | 'desc', // Default to high to low
    };
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
    sortedPortfolio() {
      let local_list = [...this.portfolio.holdings]; // Create a copy to avoid mutating props
      
      if (this.sortOrder === 'desc') {
        // High to Low (descending) - assuming sorting by weight
        local_list.sort((a, b) => b.weight - a.weight);
      } else {
        // Low to High (ascending)
        local_list.sort((a, b) => a.weight - b.weight);
      }
      
      return local_list;
    },
    shortList() {
      const query = this.searchQuery.toLowerCase();
      let filtered = this.sortedPortfolio;
      if (query) {
        filtered = this.sortedPortfolio.filter((item) =>
          item.ticker.toLowerCase().includes(query),
        );
      }
      const shortenedList = filtered.slice(
        0,
        this.$store.getters.displayLength,
      );
      return shortenedList;
    },
  },
  methods: {
    setSortOrder(order: 'asc' | 'desc') {
      this.sortOrder = order;
    },
  },
};
</script>