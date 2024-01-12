

<template>
    <TargetPortfolioView :portfolio="portfolio" :targetSize="targetSize"></TargetPortfolioView>
</template>
  
<script lang="ts">
import TargetPortfolioView from "./target_portfolio/TargetPortfolioView.vue";
import TargetPortfolioModel from './models/TargetPortfolioModel';
import TargetPortfolioElementModel from './models/TargetPortfolioElementModel';
export default {
    components: {
        TargetPortfolioView,
    },
    data() {
        return {
            targetSize: 100_000,
            portfolio: new TargetPortfolioModel({
                holdings: [
                    new TargetPortfolioElementModel(
                    {
                        ticker: 'AAPL',
                        weight: 0.5,
                    }),
                    new TargetPortfolioElementModel(
                    {
                        ticker: 'TSLA',
                        weight: 0.5,
                    }),
                ],
                source_date: '2023-01-01',
                name: 'test',
            })
        }
    }
}
</script>