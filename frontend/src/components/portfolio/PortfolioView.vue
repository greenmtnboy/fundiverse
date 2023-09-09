<template>
    <v-list class="pt-0" density="compact" v-if="portfolio.holdings.length > 0">
        <template v-for="element in shortList" :key="element.ticker">
            <PortfolioElement :targetWeight = "element.targetWeight" :value = "element.value" 
            :ticker="element.ticker"  :totalPortfolioSize="targetSize" />
        </template>
    </v-list>
</template>

<style>
.v-list-item {
    /* border: 1px solid black;
  padding: 8px;
  margin-bottom: 8px; */
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    padding: 8px;
    margin-bottom: 8px;
}

.v-list-item:hover {
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}
</style>

<script lang="ts">
import PortfolioElement from "./PortfolioElement.vue";
import CompositePortfolioModel from '../../models/CompositePortfolioModel';
import PortfolioModel from '../../models/PortfolioModel';

export default {
    name: "PortfolioView",
    components: {
        PortfolioElement,
    },
    computed: {
        // portfolioSum() {
        //   return this.portfolio.holdings.reduce((sum, holding) => sum + holding.value.value, 0);
        // },
        sortedPortfolio() {
            let local_list = this.portfolio.holdings;
            local_list.sort((a, b) => b.value.value - a.value.value)
            return local_list;
        },
        shortList() {
            const query = this.searchQuery.toLowerCase();
            const filtered = this.sortedPortfolio.filter(item => item.ticker.toLowerCase().includes(query));
            const shortenedList = filtered.slice(0, this.$store.getters.displayLength);
            return shortenedList

        }
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
            default: ''
        }
    },
};
</script>
