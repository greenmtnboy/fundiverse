<template>
  <div>
    <!-- Sort Control Toggle -->
    <div class="sort-control mb-3">
      <v-btn :variant="sortOrder === 'desc' ? 'flat' : 'outlined'" :color="sortOrder === 'desc' ? 'primary' : 'default'"
        size="small" class="sort-btn" @click="setSortOrder('desc')">
        High → Low
      </v-btn>
      <v-btn :variant="sortOrder === 'asc' ? 'flat' : 'outlined'" :color="sortOrder === 'asc' ? 'primary' : 'default'"
        size="small" class="sort-btn" @click="setSortOrder('asc')">
        Low → High
      </v-btn>
    </div>

    <!-- Portfolio List -->
    <v-list class="pt-0" density="compact" v-if="portfolio.holdings.length > 0">
      <template v-for="element in shortList" :key="element.ticker">
        <PortfolioElement :targetWeight="element.targetWeight" :value="element.value" :ticker="element.ticker"
          :totalPortfolioSize="targetSize" :appreciation="element.appreciation" :dividends="element.dividends" />
      </template>
    </v-list>
  </div>
</template>

<style>
.v-list-item {
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  padding: 8px;
  margin-bottom: 8px;
}

.v-list-item:hover {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

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
import PortfolioElement from "./PortfolioElement.vue";
import CompositePortfolioModel from "../../models/CompositePortfolioModel";
import PortfolioModel from "../../models/PortfolioModel";

export default {
  name: "PortfolioView",
  components: {
    PortfolioElement,
  },
  data() {
    return {
      sortOrder: 'desc' as 'asc' | 'desc', // Default to high to low
    };
  },
  computed: {
    sortedPortfolio() {
      let local_list = [...this.portfolio.holdings]; // Create a copy to avoid mutating props

      if (this.sortOrder === 'desc') {
        // High to Low (descending)
        local_list.sort((a, b) => b.value.value - a.value.value);
      } else {
        // Low to High (ascending)
        local_list.sort((a, b) => a.value.value - b.value.value);
      }

      return local_list;
    },
    shortList() {
      let filtered = this.sortedPortfolio;
      const query = this.searchQuery.toLowerCase();
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
  props: {
    portfolio: {
      type: [PortfolioModel, CompositePortfolioModel],
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
};
</script>