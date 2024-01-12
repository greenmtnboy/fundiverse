<template>
    <v-card title="Demo Portfolio">
        <v-list class="pt-0" density="compact" v-if="portfolio.holdings.length > 0">
            <template v-for="element in shortList" :key="element.ticker">
                <TargetPortfolioElement :element="element" :totalPortfolioSize="targetSize" />
            </template>
        </v-list>
    </v-card>
</template>

<script lang="ts">
import TargetPortfolioElement from "./TargetPortfolioElement.vue";
import TargetPortfolioModel from '../models/TargetPortfolioModel';

export default {
    name: "TargetPortfolioView",
    components: {
        TargetPortfolioElement,
    },
    data() {
        return {
            displayLength:20,
        }
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
            default: ''
        }
    },
    computed: {
        shortList() {
            const query = this.searchQuery.toLowerCase();
            const filtered = this.portfolio.holdings.filter(item => item.ticker.toLowerCase().includes(query));
            const shortenedList = filtered.slice(0, this.displayLength);
            return shortenedList

        }
    }
};
</script>
