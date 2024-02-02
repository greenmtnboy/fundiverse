

<template>
    <v-card theme="dark" class="sharp mt-10">
        <v-card-title>Create Portfolio</v-card-title>
        <v-progress-linear v-if="pythonLoading" color="primary" indeterminate></v-progress-linear>
        <v-card-subtitle>
            <v-tabs v-model="activeSelector">
                <v-tab value='index'>
                    Select Base Index
                </v-tab>
                <v-tab value='lists'>
                    Personalize By Stock List
                </v-tab>
                <v-tab value='stocks'>
                    Personalize by Stock
                </v-tab>
            </v-tabs>
        </v-card-subtitle>
        <v-card-body>
            <StockListSetter v-if="activeSelector == 'lists'" />
            <IndexSetter v-else-if="activeSelector == 'index'" />
            <StockSetter v-else-if="activeSelector == 'stocks'" />
        </v-card-body>
    </v-card>
    <v-divider />
    <v-skeleton-loader v-if="indexesLoading" type="card"></v-skeleton-loader>
    <TargetPortfolioView v-else-if="demoPortfolio.holdings" :portfolio="demoPortfolio" :targetSize="portfolioTarget">
    </TargetPortfolioView>
    
</template>
<style>
.sharp {
    border-radius: 0;
}
</style>
<script lang="ts">
import TargetPortfolioView from "./target_portfolio/TargetPortfolioView.vue";
import StockListSetter from "./target_portfolio/StockListSetter.vue";
import IndexSetter from "./target_portfolio/IndexSetter.vue"
import StockSetter from "./target_portfolio/StockSetter.vue"
import { mapGetters, mapActions } from 'vuex';

export default {
    components: {
        TargetPortfolioView,
        StockListSetter,
        IndexSetter,
        StockSetter,
    },
    data() {
        return {
            activeSelector: 'index',
        }
    },
    methods: {
        ...mapActions(['getStockLists', 'getIndexes', 'getPython']),
    },
    computed: {
        ...mapGetters(['demoPortfolio', 'portfolioTarget', 'indexesLoading', 'pythonLoading']),
    },
    mounted() {

        this.getPython().then(() => {
            this.getIndexes()
            this.getStockLists()
        })
        // this.genBackend()
    }
}
</script>