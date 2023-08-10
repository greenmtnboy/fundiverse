<template>
    <v-card class="ma-4">
        <v-card-title :key="portfolio.name" class="text-left">
            {{ portfolio.name }} <span class="text-low-emphasis"
            style = "opacity=0.5; font-size: small">({{
                    timeDisplay }})</span>
        </v-card-title>
        <v-alert type="error" v-if="error">{{ error }}</v-alert>
        <v-card-text class="text-high-emphasis text--primary ">
            <div>
                <p class="text-high-emphasis font-weight-black text--primary">A portfolio across {{
                    portfolio.components.length }} providers with target size
                    <CurrencyItem :value="{ currency: '$', value: portfolio.target_size }" />
                </p>
                <p v-if="selectedIndex">Based on index <span class="font-weight-black" :style="{ color: 'purple' }">{{
                    this.selectedIndex }}</span>
                    with {{ customizationCount }} customizations.</p>
                <p v-else :style="{color: 'orange'}"> No target index selected. Click customize to set.</p>
            </div>
            <div>
            </div>
            <v-divider class="pb-4"></v-divider>
            <v-progress-linear v-if="portfolio.loading" indeterminate color="blue-lighten-3" height="20">
            </v-progress-linear>
            <template v-else>
                <v-progress-linear color="green-lighten-3" v-model="portfolioInTargetPercent" height="20">
                    <p class="text-high-emphasis font-weight-black">
                        <CurrencyItem :loading="portfolio.loading"
                            :value="{ currency: '$', value: portfolioInTargetSum }" />, {{
                                portfolioInTargetPercent }}% of target with index stocks
                    </p>

                </v-progress-linear>
                <v-progress-linear color="blue-lighten-3" v-model="portfolioPercentOfTarget" height="20">
                    <p class="text-high-emphasis font-weight-black">
                        <CurrencyItem :loading="portfolio.loading" :value="{ currency: '$', value: portfolioSum }" />, {{
                            portfolioPercentOfTarget }}% of target including all stocks
                    </p>

                </v-progress-linear>
            </template>
        </v-card-text>
        <v-card-text class="pt-0">
            <v-divider class="pb-4 pt-0"></v-divider>

            <template v-for="sportfolio in portfolio.components" :key="sportfolio.name">
                <SubPortfolio :id="sportfolio.name" :portfolio="sportfolio" :parentName="portfolio.name" />
            </template>
            <!-- <div v-for="sportfolio in portfolio.components" :key="sportfolio.name"> 
                {{ sportfolio.holdings }}</div> -->
        </v-card-text>
        <v-card-actions>
            <ConfirmPurchase :selectedIndex="selectedIndex" :targetSize="portfolio.target_size" :cash="portfolio.cash"
                :providers="portfolio.keys" :portfolioName="portfolio.name" :disabled="portfolio.loading" />
            <v-btn @click="navigatePortfolio">
                Configure
            </v-btn>
            <ProviderLoginPopup :portfolioName="portfolio.name" :providerKeys="portfolio.keys" />

            <v-btn :disabled="portfolio.loading" @click="refresh">
                Refresh
            </v-btn>
        </v-card-actions>
    </v-card>
</template>

<script>
import CompositePortfolioModel from "@/models/CompositePortfolioModel";
import ProviderLoginPopup from "@/components/portfolio/ProviderLoginPopup.vue";
import SubPortfolio from './SubPortfolio.vue'
import CurrencyItem from '../generic/CurrencyItem.vue';
import ConfirmPurchase from "../purchase/ConfirmPurchase.vue";
import { mapActions, mapGetters } from 'vuex';
export default {
    name: "CompositePortfolioView",
    components: {
        SubPortfolio,
        ProviderLoginPopup,
        CurrencyItem,
        ConfirmPurchase
    },
    data() {
        return {
            saving: false,
            showSaveSuccess: false,
            showLoadSuccess: false,
            error: null
        }
    },
    computed: {
        ...mapGetters(['portfolioCustomizations', 'indexes']),
        // TODO: disable buy button when not logged in
        // canPurchase() {
        //     for x in this.portfolio.components {
        //         if (x.holdings.length == 0) {
        //             return false
        //         }
        //     }
        // },
        timeDisplay() {

            const options = {
                weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
                hour: 'numeric', minute: 'numeric'
            };
            const dateString = new Date(this.portfolio.refreshed_at * 1000).toLocaleDateString(undefined, options)
            if (this.error) {
                return `Refresh failed. Showing data as of ${dateString}.`
            }
            return `Refreshed ${dateString}`
        },
        customizations() {
            const custom = this.portfolioCustomizations.get(this.portfolio.name);
            return custom
        },
        customizationCount() {
            if (this.customizations) {
                return this.customizations.customizationCount

            }
            return 0;
        },
        selectedIndex() {
            if (!this.customizations) {
                return null
            }
            return this.customizations.indexPortfolio
        },
        portfolioMatchedHoldings() {
            const index = this.indexes.find((element) => element.name == this.selectedIndex)
            if (!index) {
                return []
            }
            const indexTickers = index.holdings.reduce((set, holding) => set.add(holding.ticker), new Set())
            return this.portfolio.holdings.filter((element) => indexTickers.has(element.ticker));
        },
        portfolioInTargetSum() {
            return this.portfolioMatchedHoldings.reduce((sum, holding) => sum + holding.value.value, 0);
        },
        portfolioInTargetPercent() {
            return Math.round((this.portfolioInTargetSum / this.portfolio.target_size) * 100);
        },
        portfolioSum() {
            return this.portfolio.holdings.reduce((sum, holding) => sum + holding.value.value, 0);
        },
        portfolioPercentOfTarget() {
            return Math.round((this.portfolioSum / this.portfolio.target_size) * 100);
        },

        // selectedIndex() {
        //     return this.$store.getters.selectedIndex;
        // }
    },
    props: {
        portfolio: {
            type: CompositePortfolioModel,
            required: true,
        },
    },
    methods: {
        ...mapActions(["refreshCompositePortfolio", "saveCompositePortfolios"]),
        navigatePortfolio() {
            this.$router.push({ path: `composite_portfolio/${this.portfolio.name}` })
        },
        async refresh() {
            this.error = null;
            try {
                await this.refreshCompositePortfolio({ portfolioName: this.portfolio.name, keys: this.portfolio.keys })
                await this.saveCompositePortfolios();
            } catch (e) {
                this.error = e
            }
            
        },
    }

};
</script>
