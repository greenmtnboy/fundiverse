

<template>
    <v-card theme="dark" class="sharp">
        <v-card-title>Customize Portfolio</v-card-title>
        <v-card-subtitle>
            <v-tabs v-model="activeSelector">
                <v-tab value='index'>
                    Select Base Index
                </v-tab>
                <v-tab value='lists'>
                    By Stock List
                </v-tab>
                <v-tab value='stocks'>
                    By Stock
                </v-tab>
            </v-tabs>
        </v-card-subtitle>
        <v-card-body>
            <StockListSetter v-if="activeSelector == 'lists'" />
            <IndexSetter v-else-if="activeSelector == 'index'" />
        </v-card-body>
    </v-card>
    <v-divider />
    <TargetPortfolioView :portfolio="demoPortfolio" :targetSize="portfolioTarget"></TargetPortfolioView>
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
import {mapGetters, mapActions} from 'vuex';

export default {
    components: {
        TargetPortfolioView,
        StockListSetter,
        IndexSetter,
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
        ...mapGetters(['demoPortfolio', 'portfolioTarget']),
    },
    mounted() {
        this.getStockLists()
        this.getIndexes()
        this.getPython()
        // this.genBackend()
    }
}
</script>