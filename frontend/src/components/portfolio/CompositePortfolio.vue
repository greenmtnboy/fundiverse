<template>
    <v-card class="ma-4">
        <v-card-title :key="portfolio.name" class="text-left">
            {{ portfolio.name }}
            <!-- <v-progress-circular v-if="portfolio.loading" indeterminate color="primary"></v-progress-circular> -->
            <v-progress-linear color="blue-lighten-3" v-model="portfolioPercentOfTarget" height="15">
                <span class="text-caption">{{ portfolioPercentOfTarget }}%</span>
            </v-progress-linear>
        </v-card-title>
        <v-card-text>
            <v-divider class="pb-4"></v-divider>

            <template v-for="sportfolio in portfolio.components" :key="sportfolio.name">
                <SubPortfolio :id="sportfolio.name" :portfolio="sportfolio" :parentName="portfolio.name" />
            </template>
            <!-- <div v-for="sportfolio in portfolio.components" :key="sportfolio.name"> 
                {{ sportfolio.holdings }}</div> -->
        </v-card-text>
        <v-card-actions>
            <ProviderLoginPopup :portfolioName="portfolio.name" :providerKeys="portfolio.keys" />
            <v-btn>
                Configure
            </v-btn>
            <v-btn @click="refresh">
                Refresh
            </v-btn>
        </v-card-actions>
    </v-card>
</template>

<script>
import CompositePortfolioModel from "@/models/CompositePortfolioModel";
import ProviderLoginPopup from "@/components/portfolio/ProviderLoginPopup.vue";
import SubPortfolio from './SubPortfolio.vue'
import { mapActions } from 'vuex';
export default {
    name: "CompositePortfolioView",
    components: {
        SubPortfolio,
        ProviderLoginPopup
    },
    data() {
        return {
            saving: false,
            showSaveSuccess: false,
            showLoadSuccess: false,
        }
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
    methods: {
        ...mapActions(["refreshCompositePortfolio"]),
        async refresh() {
            await this.refreshCompositePortfolio({ portfolioName: this.portfolio.name, keys: this.portfolio.keys })
        },
        async loadPortfolios() {
            this.saving = true;
            await this.loadCompositePortfolios();

            // Reset the success state after a delay
            setTimeout(() => {
                this.saving = false;
                this.showLoadSuccess = true;
            }, 1000);
            setTimeout(() => {
                this.showLoadSuccess = false;
            }, 2500);

        },
        async getPortfolios() {
            await this.refreshCompositePortfolios();
        },
    }

};
</script>
