<template>
    <v-card variant="outlined" border="grey-lighten-1" class="ma-4">
        <v-card-title :key="portfolio.name" class="text-left"  >
            {{ portfolio.name }} 
            <div class="text-h12 mb-1">
          Headline
        </div>
        <v-progress-linear color="blue-lighten-3" v-model="portfolioPercentOfTarget" height="15">
                <span class="text-caption">{{ portfolioPercentOfTarget }}%</span>
            </v-progress-linear>
        </v-card-title>
        <v-card-text>
            <v-divider class="pb-4"></v-divider>   

            <template v-for="sportfolio in portfolio.components" :key="sportfolio.name"> 
                <SubPortfolio :portfolio="sportfolio" />       
            </template>
            <!-- <div v-for="sportfolio in portfolio.components" :key="sportfolio.name"> 
                {{ sportfolio.holdings }}</div> -->
        </v-card-text>
        <v-card-actions>
      <v-btn variant="outlined">
        Add Provider
      </v-btn>
      <v-btn variant="outlined">
        Configure
      </v-btn>
    </v-card-actions>
    </v-card>
</template>

<script>
import CompositePortfolioModel from "@/models/CompositePortfolioModel";
import SubPortfolio from './SubPortfolio.vue'
export default {
    name: "PortfolioView",
    components: {
        SubPortfolio
    },
    computed: {
        portfolioSum() {
            return this.portfolio.holdings.reduce((sum, holding) => sum + holding.value.value, 0);
        },
        portfolioPercentOfTarget() {
            return Math.round((this.portfolioSum / this.portfolio.target_size) * 100);
        },
    },
    props: {
        portfolio: {
            type: CompositePortfolioModel,
            required: true,
        },
    },
};
</script>
